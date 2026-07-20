"""
Core document-generation logic: builds the prompt, calls the model, assembles
and persists the narrative. Lives outside views.py so it can be called from
both the synchronous view code path and the Celery task that actually runs it
(see documents/tasks.py::generate_document_task) without a views->tasks or
tasks->views import direction problem.
"""
import time

from ai_engine.leak_check import check_narrative
from ai_engine.model_client import ModelClient
from ai_engine.postprocess import clean_narrative
from ai_engine.prompt_builder import PROMPT_BUILDERS
from ai_engine.quality_review import (
    check_constitutional_quality,
    consistency_review,
    structural_review,
)

from .models import GeneratedDocument
from .templates_engine import get_template_text, render_template

# Doc types that use the rules-based legal template (requirement #2) instead of
# a freely-drafted narrative — the AI only writes the connecting factual body.
WARRANT_SECTIONS = {
    'search_warrant': ('affidavit_intro', 'nexus_closing'),
    'arrest_warrant': ('affidavit_intro', 'elements_closing'),
}


def _officer_profile(user) -> dict:
    """Profile fields auto-injected into every document (not in form_data)."""
    profile = {
        'full_name': user.full_name,
        'rank': user.rank,
        'badge_number': user.badge_number,
        'department_name': user.department_name,
        'department_address': user.department_address,
        'department_state': user.department_state,
        'ori': user.ori,
        'phone': user.phone_number,
        'email': user.email,
    }

    agency = user.agency
    if agency:
        from utils.storage import media_url

        profile.update({
            'agency_id': agency.id,
            'agency_name': agency.name,
            'agency_jurisdiction_type': agency.jurisdiction_type,
            'agency_state': agency.state,
            'agency_county': agency.county,
            'agency_city': agency.city,
            'agency_court_name': agency.court_name,
            'agency_judicial_district': agency.judicial_district,
            'agency_division': agency.division,
            'agency_court_caption': agency.court_caption,
            'agency_judge_title': agency.judge_title,
            'agency_prosecuting_authority': agency.prosecuting_authority,
            'agency_case_number_format': agency.case_number_format,
            'agency_default_legal_citations': agency.effective_legal_citations(),
            'agency_seal_key': agency.seal_image_key or None,
            'agency_seal_url': media_url(agency.seal_image_key) if agency.seal_image_key else None,
            'agency_requires_supervisor_review': agency.requires_supervisor_review,
            'agency_requires_prosecutor_review': agency.requires_prosecutor_review,
        })
        # Override legacy fields if agency is set
        profile['department_name'] = agency.name
        profile['department_state'] = agency.state
        profile['ori'] = agency.ori

    return profile


def _warrant_template_values(doc_type, form_data, officer):
    """Placeholder values for the fixed legal-template sections — all sourced
    directly from officer-provided facts, never from the AI."""
    values = {
        'affiant_name': officer.get('full_name', ''),
        'rank': officer.get('rank', ''),
        'agency_name': officer.get('agency_name') or officer.get('department_name', ''),
    }
    if doc_type == 'search_warrant':
        pc = form_data.get('probable_cause', {})
        place = form_data.get('place_to_search', {})
        offenses = ', '.join(
            f"{o.get('code_section', '')} ({o.get('description', '')})"
            for o in form_data.get('offenses', [])
        )
        values.update({
            'offenses': offenses,
            'place_description': place.get('description', ''),
            'nexus_to_place': pc.get('nexus_to_place', ''),
        })
    elif doc_type == 'arrest_warrant':
        offense = form_data.get('offense', {})
        values.update({
            'defendant_name': form_data.get('defendant', {}).get('full_name', ''),
            'offense_description': offense.get('brief_description', ''),
            'code_section': offense.get('code_section', ''),
        })
    return values


def _default_review_status(doc_type, agency):
    if doc_type not in WARRANT_SECTIONS or not agency:
        return GeneratedDocument.ReviewStatus.NOT_REQUIRED
    if agency.requires_supervisor_review:
        return GeneratedDocument.ReviewStatus.PENDING_SUPERVISOR
    if agency.requires_prosecutor_review:
        return GeneratedDocument.ReviewStatus.PENDING_PROSECUTOR
    return GeneratedDocument.ReviewStatus.NOT_REQUIRED


def run_generation(doc, narrative_style, temperature=0.2):
    """Build the prompt, call the model, assemble + persist the narrative. Raises on failure."""
    officer = _officer_profile(doc.user)
    builder = PROMPT_BUILDERS[doc.doc_type]
    prompt = builder(doc.form_data, officer, narrative_style)

    start = time.time()
    client = ModelClient()
    if prompt:
        ai_text = client.generate(prompt, max_tokens=3000, temperature=temperature)
        # Strip Markdown / echoed signature blocks the model may add (model-independent).
        ai_text = clean_narrative(ai_text, officer)
    else:
        # No facts supplied for the AI to organize (e.g. an arrest warrant with
        # no probable-cause narrative) — the fixed template sections still stand.
        ai_text = ''
    elapsed = int((time.time() - start) * 1000)

    if doc.doc_type in WARRANT_SECTIONS:
        # Rules-based template: fixed, pre-approved legal sections (requirement
        # #2) with jurisdiction-specific phrasing (requirement #3) wrap the
        # AI-authored factual narrative. The AI never writes the legal-
        # conclusion sentences — see ai_engine/prompt_builder.py.
        intro_key, closing_key = WARRANT_SECTIONS[doc.doc_type]
        agency = doc.user.agency
        jurisdiction_override = doc.form_data.get('court', {}).get('jurisdiction_type_override')
        values = _warrant_template_values(doc.doc_type, doc.form_data, officer)

        intro = render_template(
            get_template_text(agency, doc.doc_type, intro_key, jurisdiction_override), values)
        closing = render_template(
            get_template_text(agency, doc.doc_type, closing_key, jurisdiction_override), values)

        doc.narrative_body = ai_text
        assembled = '\n\n'.join(part.strip() for part in [intro, ai_text, closing] if part and part.strip())
        doc.review_status = _default_review_status(doc.doc_type, agency)
    else:
        doc.narrative_body = ai_text
        assembled = ai_text

    # Deterministic post-generation leak/hallucination check — run against the
    # AI-authored portion only; the templated intro/closing can't hallucinate.
    doc.leak_flags = check_narrative(doc.narrative_body, doc.form_data, officer)

    # Constitutional Quality Review: deterministic structural/consistency checks
    # (never depend on the LLM, so they can't silently fail open) run against
    # form_data/the assembled text, plus the LLM-based review — merged into one
    # flag list.
    doc.quality_flags = (
        structural_review(doc.doc_type, doc.form_data)
        + consistency_review(doc.doc_type, assembled, doc.form_data)
        + check_constitutional_quality(doc.doc_type, assembled)
    )

    doc.ai_narrative = assembled
    doc.status = GeneratedDocument.Status.COMPLETED
    doc.generation_time_ms = elapsed
    doc.model_used = client.model_name
    doc.save()
    return assembled

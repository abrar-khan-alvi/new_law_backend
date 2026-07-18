"""
RAG-aware prompt builders (hardened against fact-leakage).

Each builder assembles the model instruction from:
  1. a task framing + style (person) instruction,
  2. the auto-injected officer/department profile,
  3. read-only structured context (grounding — names, roles, offenses),
  4. a STYLE REFERENCE retrieved from this agency's indexed training documents
     (pgvector RAG) — SANITIZED and framed as style-only, placed BEFORE the facts,
  5. the `ai_fuel` FACTS the model must expand — delimited and placed LAST so they
     are the freshest, authoritative context,
  6. a closing anti-leak instruction.

Anti-leakage design (an 8B model will otherwise copy concrete details from a
similar example):
  - retrieved chunks are run through `_sanitize_examples()` which redacts emails,
    phones, SSNs, currency amounts, dates, times, case/ID numbers, and IPs;
  - the examples are explicitly framed as "different, unrelated cases — style only";
  - facts come AFTER the examples (recency), and a final instruction forbids
    importing any entity not present in the FACTS block.

This reduces but cannot fully guarantee zero leakage; a post-generation entity
check (comparing narrative entities to form_data) is the belt-and-suspenders
follow-up. Retrieval is best-effort: if nothing is indexed (or RAG fails) the
builder degrades to a clean, example-free prompt.

Signature for all builders (unchanged): (form_data, officer, narrative_style) -> str
"""
import logging
import re

logger = logging.getLogger(__name__)

# ── PII / identifier redaction (applied to retrieved style examples) ──────
# Order matters: more specific patterns first so they win over generic ones.
_REDACTIONS = [
    (re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b'), '[EMAIL]'),
    (re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b'), '[IP]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),
    (re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), '[PHONE]'),
    (re.compile(r'\$\s?\d[\d,]*(?:\.\d+)?'), '[AMOUNT]'),
    # Month-name dates: "January 6, 2026"
    (re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b', re.I), '[DATE]'),
    (re.compile(r'\b\d{4}-\d{2}-\d{2}\b'), '[DATE]'),            # ISO date
    (re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'), '[DATE]'),     # slash date
    (re.compile(r'\bIR\s*#?\s*\d+\b', re.I), '[CASE]'),         # incident #
    (re.compile(r'\b\d{2}-\d{5,6}\b'), '[CASE]'),              # e.g. 18-100301
    (re.compile(r'\b\d{1,2}:\d{2}\s*(?:[AaPp]\.?[Mm]\.?)?\b'), '[TIME]'),  # HH:MM
    (re.compile(r'\b\d{3,4}\s*hours?\b', re.I), '[TIME]'),     # "1930 hours"
    (re.compile(r'\b\d{6,}\b'), '[ID]'),                       # long id/badge runs
]

_ANTI_LEAK = (
    "\nIMPORTANT — write the narrative using ONLY the facts in the FACTS block "
    "above. The writing samples described DIFFERENT, unrelated cases and were "
    "provided solely to guide tone, structure, paragraph flow, and terminology. "
    "Do NOT import any name, person, place, address, item, brand, amount, date, "
    "time, or event from the samples unless it also appears in the FACTS block.\n"
)

_OUTPUT_RULES = (
    "OUTPUT FORMAT: Write plain narrative prose only. Do NOT use Markdown, "
    "asterisks, bold, bullet points, or headings/labels such as 'Narrative:', "
    "'NARRATIVE', or 'End of Narrative'. Do NOT restate or append the officer's "
    "name, badge, rank, ORI, department, or any signature block — the document "
    "template adds those automatically.\n\n"
)


def _sanitize_examples(text: str) -> str:
    for pattern, repl in _REDACTIONS:
        text = pattern.sub(repl, text)
    return text


def _officer_block(officer: dict) -> str:
    agency_name = officer.get('agency_name') or officer.get('department_name', '')
    return (
        f"Officer: {officer.get('full_name', '')}\n"
        f"Rank/Title: {officer.get('rank', '')}\n"
        f"Badge: {officer.get('badge_number', '')}\n"
        f"Department/Agency: {agency_name}\n"
        f"ORI: {officer.get('ori', '')}\n"
    )

def _agency_context(officer: dict) -> str:
    if not officer.get('agency_name'):
        return ""
        
    jurisdiction = officer.get('agency_jurisdiction_type', 'state').capitalize()
    state = officer.get('agency_state', 'Unknown State')
    county = officer.get('agency_county', '')
    default_citations = officer.get('agency_default_legal_citations', '')
    
    ctx = f"Agency Jurisdiction Type: {jurisdiction} ({state}"
    if county:
        ctx += f", {county} County"
    ctx += ")\n"
    
    if default_citations:
        ctx += f"Default Legal Citations to consider: {default_citations}\n"
        
    return f"\nJURISDICTION CONTEXT (Apply {jurisdiction} formatting rules):\n{ctx}"


def _style_instruction(narrative_style: str) -> str:
    if narrative_style == 'third_person':
        return "Write in the third person, referring to the officer by name/title."
    return "Write in the first person (I, my), from the officer's perspective."


def _style_reference(query: str, doc_type: str) -> str:
    """
    Pull the most similar excerpts from this agency's indexed training docs,
    SANITIZE them, and wrap them as a style-only reference. Returns '' when
    nothing is indexed or RAG fails.
    """
    try:
        from .rag_pipeline import retrieve_style_examples
        examples = retrieve_style_examples(query, doc_type=doc_type)
    except Exception as exc:  # noqa: BLE001 — RAG is an enhancement, never a hard dependency
        logger.warning('RAG style retrieval failed (%s); continuing without examples', exc)
        return ''

    if not examples.strip():
        return ''

    examples = _sanitize_examples(examples)
    label = doc_type.replace('_', ' ')
    return (
        f"\nWRITING-STYLE SAMPLES — excerpts from prior {label} documents written "
        "by this agency, shown ONLY so you can match their tone, sentence structure, "
        "paragraph flow, and terminology. These describe DIFFERENT, unrelated cases. "
        "Identifiers have been redacted as [TAGS]. Treat NONE of their content as "
        "facts for the current report.\n"
        "<<<BEGIN STYLE SAMPLES\n"
        f"{examples}\n"
        "END STYLE SAMPLES>>>\n"
    )


# ── Incident report ──────────────────────────────────────────────────
def build_incident_report_prompt(form_data, officer, narrative_style='first_person'):
    facts = form_data.get('facts', {})
    incident = form_data.get('incident', {})
    parties = form_data.get('involved_parties', [])

    categories = ', '.join(incident.get('categories', []))
    party_lines = '\n'.join(
        f"- {p.get('role', 'other')}: {p.get('full_name', '')}"
        + (f" (ID {p['id_number']})" if p.get('id_number') else '')
        for p in parties
    ) or '- (none listed)'

    header = (
        "You are assisting a law enforcement officer in drafting the NARRATIVE "
        "section of an incident report. Be objective, chronological, and "
        "professional. Use 24-hour time.\n\n"
        f"{_OUTPUT_RULES}"
        f"{_style_instruction(narrative_style)}\n\n"
        "Officer on the report (context only — do NOT reproduce as a signature):\n"
        f"{_officer_block(officer)}\n"
        "Incident context (for accuracy):\n"
        f"- Categories: {categories or 'N/A'}\n"
        f"- Date/Time: {incident.get('date', '')} {incident.get('time', '')}\n"
        f"- Location: {incident.get('location', '')}\n"
        "Involved parties:\n"
        f"{party_lines}\n"
    )

    query = ' '.join(filter(None, [facts.get('what', ''), facts.get('who', ''), categories]))
    style = _style_reference(query, 'incident_report')

    facts_block = (
        "\n=== FACTS (the ONLY source of truth for this report) ===\n"
        f"- Who: {facts.get('who', '')}\n"
        f"- What: {facts.get('what', '')}\n"
        f"- When: {facts.get('when', '')}\n"
        f"- Where: {facts.get('where', '')}\n"
        f"- Why: {facts.get('why', '')}\n"
        f"- How: {facts.get('how', '')}\n"
        f"- Officer actions: {facts.get('officer_actions', '')}\n"
        f"- Additional notes: {facts.get('additional_notes', '')}\n"
        "=== END FACTS ===\n"
    )

    return header + style + facts_block + _ANTI_LEAK + "\nWrite the narrative now:"


# ── Search warrant ───────────────────────────────────────────────────
# NOTE: search/arrest warrants use a rules-based template for the legal
# sections (see documents/templates_engine.py) — the AI's job here is narrowed
# to organizing the officer's facts into ONE factual investigation narrative.
# It never drafts the legal-conclusion sentences (nexus/elements/citations);
# those are fixed, pre-approved text with placeholders filled directly from
# form_data, assembled in documents/views.py::_run_generation.
def build_search_warrant_prompt(form_data, officer, narrative_style='first_person'):
    pc = form_data.get('probable_cause', {})
    offenses = ', '.join(
        f"{o.get('code_section', '')} ({o.get('description', '')})"
        for o in form_data.get('offenses', [])
    )
    place = form_data.get('place_to_search', {})

    header = (
        "You are assisting a law enforcement officer with a search warrant "
        "affidavit. Your ONLY job is to write the INVESTIGATION NARRATIVE — a "
        "clear, chronological, factual account of the investigation (who did "
        "what, when, where, and how it was learned). Organize the officer's "
        "facts into readable prose; do NOT invent legal language. Do NOT state "
        "a probable-cause conclusion, do NOT argue the nexus to the place to be "
        "searched, and do NOT cite statutes or write a closing paragraph — a "
        "fixed, pre-approved legal section is appended automatically after "
        "your narrative and already covers that.\n\n"
        f"{_OUTPUT_RULES}"
        f"{_style_instruction(narrative_style)}\n\n"
        "Affiant officer (context only — do NOT reproduce as a signature):\n"
        f"{_officer_block(officer)}\n"
        f"{_agency_context(officer)}"
    )

    query = ' '.join(filter(None, [pc.get('investigation_summary', ''), offenses,
                                   pc.get('nexus_to_place', '')]))
    style = _style_reference(query, 'search_warrant')

    facts_block = (
        "\n=== FACTS (the ONLY source of truth for this narrative) ===\n"
        f"- Offenses: {offenses}\n"
        f"- Place to search: {place.get('description', '')} — {place.get('address', '')}\n"
        f"- Affiant background: {pc.get('affiant_background', '')}\n"
        f"- Investigation summary: {pc.get('investigation_summary', '')}\n"
        f"- Timeline: {'; '.join(pc.get('timeline', []))}\n"
        f"- Prior warrants: {pc.get('prior_warrants', '') or 'none'}\n"
        "=== END FACTS ===\n"
        "(Note: the nexus-to-place reasoning is handled by the fixed closing "
        "section, not by you — do not restate it here.)\n"
    )

    if not (pc.get('investigation_summary') or pc.get('affiant_background') or pc.get('timeline')):
        # No narrative facts supplied — nothing for the AI to organize;
        # _run_generation will skip the AI call and use the template alone.
        return ''

    return header + style + facts_block + _ANTI_LEAK + (
        "\nWrite ONLY the investigation narrative now (no conclusion, no citations):"
    )


# ── Arrest warrant ───────────────────────────────────────────────────
def build_arrest_warrant_prompt(form_data, officer, narrative_style='first_person'):
    offense = form_data.get('offense', {})
    pc = form_data.get('probable_cause', {})

    header = (
        "You are assisting a law enforcement officer with an arrest warrant "
        "affidavit. Your ONLY job is to write the INVESTIGATION NARRATIVE — a "
        "clear, chronological, factual account of the investigation supporting "
        "the arrest. Organize the officer's facts into readable prose; do NOT "
        "invent legal language. Do NOT state a probable-cause conclusion, do "
        "NOT recite the elements of the offense, and do NOT cite statutes — a "
        "fixed, pre-approved legal section is appended automatically after "
        "your narrative and already covers that.\n\n"
        f"{_OUTPUT_RULES}"
        f"{_style_instruction(narrative_style)}\n\n"
        "Affiant officer (context only — do NOT reproduce as a signature):\n"
        f"{_officer_block(officer)}\n"
        f"{_agency_context(officer)}"
    )

    query = ' '.join(filter(None, [offense.get('brief_description', ''), pc.get('facts', '')]))
    style = _style_reference(query, 'arrest_warrant')

    facts_block = (
        "\n=== FACTS (the ONLY source of truth for this narrative) ===\n"
        f"- Defendant: {form_data.get('defendant', {}).get('full_name', '')}\n"
        f"- Offense: {offense.get('code_section', '')} — {offense.get('brief_description', '')}\n"
        f"- Facts: {pc.get('facts', '') or '(none)'}\n"
        f"- Timeline: {'; '.join(pc.get('timeline', []))}\n"
        "=== END FACTS ===\n"
    )

    if not (pc.get('facts') or pc.get('timeline')):
        # No narrative facts supplied at all — nothing for the AI to organize;
        # _run_generation will skip the AI call and use the template alone.
        return ''

    return header + style + facts_block + _ANTI_LEAK + (
        "\nWrite ONLY the investigation narrative now (no conclusion, no citations):"
    )


PROMPT_BUILDERS = {
    'incident_report': build_incident_report_prompt,
    'search_warrant': build_search_warrant_prompt,
    'arrest_warrant': build_arrest_warrant_prompt,
}

"""
Rules-based legal-language templates for search/arrest warrants.

Client requirement: "Rather than asking a large language model to generate a
warrant from scratch, the platform should use rules-based, pre-approved legal
templates populated by AI. The AI's responsibility is to organize
officer-provided facts into predefined legal sections, not invent legal
language."

The sections below (`affidavit_intro`, `nexus_closing`, `elements_closing`) are
fixed legal phrasing with named {placeholder} tokens, filled directly from
officer-provided facts (nexus reasoning, statute citations, defendant name —
all things the officer already typed into the intake form). None of this text
is authored by the AI; see `ai_engine/prompt_builder.py`, which only drafts the
connecting factual narrative that sits between the intro and the closing.

DEFAULT_TEMPLATES is the built-in fallback so the system works with zero DB
rows. It is generic starting language, NOT legally reviewed — an agency's own
counsel should review/replace it (via the WarrantTemplate model, admin-only,
either per-agency or per-JurisdictionProfile) before real filings.
"""
from .models import WarrantTemplate

DEFAULT_TEMPLATES = {
    'search_warrant': {
        'federal': {
            'affidavit_intro': (
                "Your affiant, {affiant_name}, a {rank} with {agency_name}, being first duly "
                "sworn, deposes and states as follows in support of an application for a search "
                "warrant pursuant to Rule 41 of the Federal Rules of Criminal Procedure:"
            ),
            'nexus_closing': (
                "Based on the foregoing facts, your affiant submits that probable cause exists "
                "to believe that evidence of the offense(s) of {offenses} is presently located "
                "at {place_description}, in that {nexus_to_place}. Your affiant therefore "
                "requests that a search warrant be issued for the above-described premises."
            ),
        },
        'state': {
            'affidavit_intro': (
                "Your affiant, {affiant_name}, a {rank} with {agency_name}, being first duly "
                "sworn, states the following under oath in support of an application for a "
                "search warrant:"
            ),
            'nexus_closing': (
                "Based on the foregoing facts, your affiant respectfully submits that probable "
                "cause exists to believe that evidence of the offense(s) of {offenses} will be "
                "found at {place_description}, in that {nexus_to_place}."
            ),
        },
        'municipal': {
            'affidavit_intro': (
                "Your affiant, {affiant_name}, a {rank} with {agency_name}, being first duly "
                "sworn, states the following under oath in support of an application for a "
                "search warrant to be issued by this court:"
            ),
            'nexus_closing': (
                "Based on the foregoing facts, your affiant respectfully submits that probable "
                "cause exists to believe that evidence of the offense(s) of {offenses} will be "
                "found at {place_description}, in that {nexus_to_place}."
            ),
        },
    },
    'arrest_warrant': {
        'federal': {
            'affidavit_intro': (
                "Your affiant, {affiant_name}, a {rank} with {agency_name}, being first duly "
                "sworn, states as follows in support of a criminal complaint and application "
                "for an arrest warrant:"
            ),
            'elements_closing': (
                "Based on the foregoing, your affiant believes there is probable cause to "
                "believe that {defendant_name} committed the offense of {offense_description}, "
                "in violation of {code_section}."
            ),
        },
        'state': {
            'affidavit_intro': (
                "Your affiant, {affiant_name}, a {rank} with {agency_name}, being first duly "
                "sworn, states the following under oath in support of an application for an "
                "arrest warrant:"
            ),
            'elements_closing': (
                "Based on the foregoing, your affiant believes there is probable cause to "
                "believe that {defendant_name} committed the offense of {offense_description}, "
                "in violation of {code_section}."
            ),
        },
        'municipal': {
            'affidavit_intro': (
                "Your affiant, {affiant_name}, a {rank} with {agency_name}, being first duly "
                "sworn, states the following under oath in support of an application for an "
                "arrest warrant:"
            ),
            'elements_closing': (
                "Based on the foregoing, your affiant believes there is probable cause to "
                "believe that {defendant_name} committed the offense of {offense_description}, "
                "in violation of {code_section}."
            ),
        },
    },
}


class _SafeDict(dict):
    def __missing__(self, key):
        return ''


def render_template(template_text: str, values: dict) -> str:
    """Fill {placeholder} tokens; never raises on a malformed/edited template —
    an admin's typo in a custom WarrantTemplate must not break generation."""
    try:
        return template_text.format_map(_SafeDict(values))
    except (ValueError, IndexError, KeyError):
        return template_text


def get_template_text(agency, doc_type: str, section_key: str, jurisdiction_override: str = None) -> str:
    """
    Resolution order: agency-specific override -> agency's jurisdiction profile
    -> seeded global default row (admin-editable, varies by jurisdiction_type)
    -> built-in Python fallback. Works with zero DB rows.
    """
    if agency:
        row = WarrantTemplate.objects.filter(
            agency=agency, doc_type=doc_type, section_key=section_key,
        ).first()
        if row:
            return row.template_text
        if agency.jurisdiction_profile_id:
            row = WarrantTemplate.objects.filter(
                jurisdiction_profile=agency.jurisdiction_profile,
                doc_type=doc_type, section_key=section_key,
            ).first()
            if row:
                return row.template_text

    jurisdiction_type = jurisdiction_override or (agency.jurisdiction_type if agency else None) or 'state'

    row = WarrantTemplate.objects.filter(
        agency__isnull=True, jurisdiction_profile__isnull=True,
        doc_type=doc_type, section_key=section_key, jurisdiction_type=jurisdiction_type,
    ).first()
    if row:
        return row.template_text

    by_doc_type = DEFAULT_TEMPLATES.get(doc_type, {})
    return (by_doc_type.get(jurisdiction_type) or by_doc_type.get('state', {})).get(section_key, '')

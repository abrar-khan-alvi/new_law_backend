"""
INTERIM prompt builders.

These assemble a basic instruction prompt from the `ai_fuel` portions of
form_data (see docs/FORM_DATA_SCHEMAS.md) plus the officer profile. They are
intentionally simple — the polished, template-aware prompt engineering is a
separate planned task. Keep call signatures stable so swapping in the real
builders later requires no view changes.

Signature for all builders: (form_data: dict, officer: dict, narrative_style: str) -> str
"""


def _officer_block(officer: dict) -> str:
    return (
        f"Officer: {officer.get('full_name', '')}\n"
        f"Rank/Title: {officer.get('rank', '')}\n"
        f"Badge: {officer.get('badge_number', '')}\n"
        f"Department: {officer.get('department_name', '')}\n"
        f"ORI: {officer.get('ori', '')}\n"
    )


def _style_instruction(narrative_style: str) -> str:
    if narrative_style == 'third_person':
        return "Write in the third person, referring to the officer by name/title."
    return "Write in the first person (I, my), from the officer's perspective."


def build_incident_report_prompt(form_data, officer, narrative_style='first_person'):
    facts = form_data.get('facts', {})
    return (
        "You are assisting a law enforcement officer in drafting the NARRATIVE "
        "section of an incident report. Use only the facts provided; do not invent "
        "details. Be objective, chronological, and professional.\n\n"
        f"{_style_instruction(narrative_style)}\n\n"
        f"{_officer_block(officer)}\n"
        "Facts:\n"
        f"- Who: {facts.get('who', '')}\n"
        f"- What: {facts.get('what', '')}\n"
        f"- When: {facts.get('when', '')}\n"
        f"- Where: {facts.get('where', '')}\n"
        f"- Why: {facts.get('why', '')}\n"
        f"- How: {facts.get('how', '')}\n"
        f"- Officer actions: {facts.get('officer_actions', '')}\n"
        f"- Additional notes: {facts.get('additional_notes', '')}\n\n"
        "Write the narrative now:"
    )


def build_search_warrant_prompt(form_data, officer, narrative_style='first_person'):
    pc = form_data.get('probable_cause', {})
    offenses = ', '.join(
        f"{o.get('code_section', '')} ({o.get('description', '')})"
        for o in form_data.get('offenses', [])
    )
    return (
        "You are assisting a law enforcement officer in drafting the AFFIDAVIT "
        "(statement of probable cause) for a search warrant. Use only the facts "
        "provided; do not invent details. Be precise and factual.\n\n"
        f"{_style_instruction(narrative_style)}\n\n"
        f"{_officer_block(officer)}\n"
        f"Offenses: {offenses}\n"
        f"Place to search: {form_data.get('place_to_search', {}).get('description', '')}\n"
        f"Affiant background: {pc.get('affiant_background', '')}\n"
        f"Investigation summary: {pc.get('investigation_summary', '')}\n"
        f"Timeline: {'; '.join(pc.get('timeline', []))}\n"
        f"Nexus to place: {pc.get('nexus_to_place', '')}\n\n"
        "Write the statement of probable cause now:"
    )


def build_arrest_warrant_prompt(form_data, officer, narrative_style='first_person'):
    offense = form_data.get('offense', {})
    pc = form_data.get('probable_cause', {})
    return (
        "You are assisting a law enforcement officer with an arrest warrant. "
        "Draft a concise, formal offense description and, if facts are provided, "
        "a short supporting probable-cause statement. Use only the facts provided.\n\n"
        f"{_style_instruction(narrative_style)}\n\n"
        f"{_officer_block(officer)}\n"
        f"Defendant: {form_data.get('defendant', {}).get('full_name', '')}\n"
        f"Offense: {offense.get('code_section', '')} — {offense.get('brief_description', '')}\n"
        f"Facts: {pc.get('facts', '')}\n"
        f"Timeline: {'; '.join(pc.get('timeline', []))}\n\n"
        "Write the offense description (and probable-cause statement if applicable) now:"
    )


PROMPT_BUILDERS = {
    'incident_report': build_incident_report_prompt,
    'search_warrant': build_search_warrant_prompt,
    'arrest_warrant': build_arrest_warrant_prompt,
}

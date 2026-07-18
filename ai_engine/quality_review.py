import json
import logging
from typing import Dict, List

from .leak_check import _normalize
from .model_client import ModelClient

logger = logging.getLogger(__name__)

QUALITY_PROMPTS = {
    'search_warrant': """
You are a Constitutional Quality Review system for Law Enforcement Search Warrants.
Review the following Search Warrant probable cause affidavit.
Identify if it is missing any of the following critical elements:
1. Missing statutory citations or references to the specific crime.
2. Missing or weak probable cause statements linking the suspect to the crime.
3. Weak nexus language (failing to establish why evidence is likely to be found at the specific location).
4. Missing descriptions of Attachment A (the place to be searched) or Attachment B (the items to be seized).
5. Missing affiant information (the affiant's name, rank/title, or agency is not identified).
6. Blank officer-entered factual sections or incomplete dates/times.

If the narrative satisfies all requirements, respond exactly with an empty JSON array: []
If the narrative is missing elements or has issues, return a JSON array of objects, each containing:
- "issue": A short phrase describing the problem (e.g. "Missing nexus language")
- "detail": A 1-2 sentence explanation of what is missing.

Respond ONLY with valid JSON. No markdown formatting, no backticks.
""",
    'arrest_warrant': """
You are a Constitutional Quality Review system for Law Enforcement Arrest Warrants.
Review the following Arrest Warrant probable cause affidavit.
Identify if it is missing any of the following critical elements:
1. Missing statutory citations or references to the specific crime.
2. Missing elements of the offense.
3. Missing or weak probable cause statements linking the suspect to the crime.
4. Blank officer-entered factual sections or incomplete dates/times.
5. Missing affiant information (the affiant's name, rank/title, or agency is not identified).

If the narrative satisfies all requirements, respond exactly with an empty JSON array: []
If the narrative is missing elements or has issues, return a JSON array of objects, each containing:
- "issue": A short phrase describing the problem (e.g. "Missing elements of offense")
- "detail": A 1-2 sentence explanation of what is missing.

Respond ONLY with valid JSON. No markdown formatting, no backticks.
"""
}

# form_data paths that must be non-blank per doc_type, checked deterministically
# (never depends on the LLM, so it can't silently fail open). Each entry is
# (dotted path, human label).
_REQUIRED_FIELDS = {
    'search_warrant': [
        ('offenses', 'Offense(s)'),
        ('place_to_search.description', 'Place to be searched (Attachment A)'),
        ('probable_cause.affiant_background', "Affiant's background"),
        ('probable_cause.investigation_summary', 'Investigation summary'),
        ('probable_cause.nexus_to_place', 'Nexus to place'),
    ],
    'arrest_warrant': [
        ('defendant.full_name', "Defendant's name"),
        ('offense.code_section', 'Statutory citation'),
        ('offense.brief_description', 'Offense description'),
    ],
}


def _dig(data: dict, path: str):
    cur = data
    for part in path.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def structural_review(doc_type: str, form_data: dict) -> List[Dict]:
    """
    Deterministic pre-flight check — runs before generation, never depends on
    the LLM. Flags required fields that are blank, so a missing fact is caught
    even if the LLM-based review below fails entirely.
    """
    flags = []
    for path, label in _REQUIRED_FIELDS.get(doc_type, []):
        value = _dig(form_data, path)
        if not value:
            flags.append({
                'issue': f'Blank required field: {label}',
                'detail': f'"{label}" was not provided and is required for a {doc_type.replace("_", " ")}.',
                'source': 'structural',
            })
    return flags


def consistency_review(doc_type: str, narrative: str, form_data: dict) -> List[Dict]:
    """
    Deterministic check that the defendant's name (arrest warrants) appears,
    consistently, in the final assembled document text — catches the client's
    "inconsistent names" concern (e.g. a customized WarrantTemplate that drops
    the {defendant_name} placeholder). Reuses the same normalization as
    ai_engine.leak_check rather than inventing new text-matching logic. Call
    this against the fully ASSEMBLED narrative (template sections + AI body),
    not just the AI-authored portion, since the name lives in the template.
    """
    flags = []
    norm_narrative = _normalize(narrative or '')

    if doc_type == 'arrest_warrant':
        name = form_data.get('defendant', {}).get('full_name')
        if name and _normalize(name) not in norm_narrative:
            flags.append({
                'issue': 'Inconsistent defendant name',
                'detail': f'Defendant name "{name}" does not appear anywhere in the generated document text.',
                'source': 'structural',
            })

    return flags


def check_constitutional_quality(doc_type: str, narrative: str) -> List[Dict]:
    """
    Run an LLM-based Constitutional Quality Review on the generated warrant narrative.
    Returns a list of flags (e.g., [{'issue': '...', 'detail': '...', 'source': 'llm'}]).
    Fails CLOSED: any error here returns a flag saying review could not complete,
    never a silent "no issues found".
    """
    if not narrative.strip():
        return [{'issue': 'Blank narrative', 'detail': 'The narrative is completely blank.', 'source': 'system'}]

    prompt_template = QUALITY_PROMPTS.get(doc_type)
    if not prompt_template:
        # We only do quality checks on warrants for now.
        return []

    full_prompt = f"{prompt_template.strip()}\n\nNarrative:\n{narrative}"

    client = ModelClient()
    response_text = ''
    try:
        # Use a low temperature for strict, deterministic checking
        response_text = client.generate(full_prompt, max_tokens=1000, temperature=0.0)

        # Clean markdown if model still output it
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        flags = json.loads(cleaned)
        if isinstance(flags, dict) and "flags" in flags:
            flags = flags["flags"]
        if not isinstance(flags, list):
            raise ValueError(f'Unexpected JSON structure: {flags!r}')
        for f in flags:
            f.setdefault('source', 'llm')
        return flags
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Quality review failed to parse JSON (%s): %s", e, response_text)
        return [{
            'issue': 'Quality review incomplete',
            'detail': 'Automated constitutional review could not be completed (unreadable AI response); manual review is required before filing.',
            'source': 'system',
        }]
    except Exception as e:  # noqa: BLE001
        logger.error("Error during Constitutional Quality Review: %s", e)
        return [{
            'issue': 'Quality review incomplete',
            'detail': 'Automated constitutional review could not be completed due to a system error; manual review is required before filing.',
            'source': 'system',
        }]

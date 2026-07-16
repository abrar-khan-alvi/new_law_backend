import json
import logging
from typing import List, Dict

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

If the narrative satisfies all requirements, respond exactly with an empty JSON array: []
If the narrative is missing elements or has issues, return a JSON array of objects, each containing:
- "issue": A short phrase describing the problem (e.g. "Missing elements of offense")
- "detail": A 1-2 sentence explanation of what is missing.

Respond ONLY with valid JSON. No markdown formatting, no backticks.
"""
}

def check_constitutional_quality(doc_type: str, narrative: str) -> List[Dict]:
    """
    Run an LLM-based Constitutional Quality Review on the generated warrant narrative.
    Returns a list of flags (e.g., [{'issue': '...', 'detail': '...'}]).
    """
    if not narrative.strip():
        return [{'issue': 'Blank narrative', 'detail': 'The narrative is completely blank.'}]
        
    prompt_template = QUALITY_PROMPTS.get(doc_type)
    if not prompt_template:
        # We only do quality checks on warrants for now.
        return []
        
    full_prompt = f"{prompt_template.strip()}\n\nNarrative:\n{narrative}"
    
    client = ModelClient()
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
        if isinstance(flags, list):
            return flags
        elif isinstance(flags, dict) and "flags" in flags:
            return flags["flags"]
        else:
            logger.warning("Quality review returned unexpected JSON structure: %s", flags)
            return []
    except json.JSONDecodeError:
        logger.warning("Quality review failed to parse JSON: %s", response_text)
        return []
    except Exception as e:
        logger.error("Error during Constitutional Quality Review: %s", e)
        return []

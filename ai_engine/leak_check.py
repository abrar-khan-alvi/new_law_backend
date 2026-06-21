"""
Post-generation leak / hallucination check.

After the model writes a narrative we verify, with deterministic (non-AI) rules,
that every CONCRETE detail in the narrative is grounded in what the officer
actually provided (form_data + officer profile). Anything ungrounded is flagged
as a possible hallucination or a fact leaked from a RAG style sample.

Scope (high precision, low false-positives): proper nouns (names/places/brands),
numbers/amounts, and contact identifiers (emails/phones/SSNs). It does NOT try to
catch common-word descriptor leaks (e.g. "black, leather-like") — that needs heavy
NLP and produces too many false positives to be useful.

It FLAGS, it does not rewrite: returns a list of {type, value} dicts for officer
review. The narrative is never mutated here.
"""
import re

# Capitalized tokens that are sentence connectors / structural — never "facts".
_STOPWORDS = {
    'the', 'a', 'an', 'at', 'on', 'in', 'of', 'to', 'and', 'or', 'but', 'for',
    'with', 'as', 'by', 'from', 'into', 'upon', 'after', 'before', 'during',
    'this', 'that', 'these', 'those', 'he', 'she', 'they', 'it', 'i', 'we',
    'mr', 'ms', 'mrs', 'dr', 'no', 'narrative', 'incident', 'report',
    'badge', 'number', 'id', 'case', 'officer', 'police', 'department',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
}

# Abbreviation ⇄ full-word equivalences so "Main St" ~ "Main Street" isn't flagged.
_ABBREV = {
    'st': 'street', 'ave': 'avenue', 'av': 'avenue', 'rd': 'road',
    'blvd': 'boulevard', 'dr': 'drive', 'ln': 'lane', 'ct': 'court',
    'pkwy': 'parkway', 'hwy': 'highway', 'ste': 'suite', 'apt': 'apartment',
    'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
    'mr': 'mr', 'ms': 'ms',
}


def _canon(token: str) -> str:
    return _ABBREV.get(token, token)


_PROPER_NOUN = re.compile(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b')
_NUMBER = re.compile(r'\$?\d[\d,]*(?:\.\d+)?')
_EMAIL = re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b')
_PHONE = re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
_SSN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

# Digits-only stripper for robust number comparison ("$400" ~ "400").
_DIGITS = re.compile(r'\D')


def _normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def _flatten(value, out: list):
    if isinstance(value, dict):
        for v in value.values():
            _flatten(v, out)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _flatten(v, out)
    elif value is not None:
        out.append(str(value))


def grounded_corpus(form_data: dict, officer: dict) -> str:
    """All officer-provided text, normalized into one searchable blob."""
    parts: list = []
    _flatten(form_data, parts)
    _flatten(officer, parts)
    return _normalize(' '.join(parts))


def check_narrative(narrative: str, form_data: dict, officer: dict) -> list[dict]:
    """Return a list of ungrounded details: [{'type': ..., 'value': ...}, ...]."""
    if not narrative:
        return []

    corpus = grounded_corpus(form_data, officer)
    corpus_tokens = set(_canon(t) for t in corpus.split())
    corpus_digits = set(_DIGITS.sub('', t) for t in corpus.split() if any(c.isdigit() for c in t))

    flags: list[dict] = []
    seen: set = set()

    def add(kind, value):
        key = (kind, value.lower())
        if key not in seen:
            seen.add(key)
            flags.append({'type': kind, 'value': value})

    # ── Contact identifiers (highest confidence) ─────────────────────
    for rx, kind in ((_EMAIL, 'email'), (_SSN, 'ssn'), (_PHONE, 'phone')):
        for m in rx.findall(narrative):
            if _normalize(m) not in corpus:
                add(kind, m if isinstance(m, str) else m[0])

    # ── Proper nouns (names / places / brands) ───────────────────────
    # Skip the token that starts a sentence (capitalization there is grammatical).
    sentence_starts = {
        _normalize(s.strip().split(' ')[0])
        for s in re.split(r'(?<=[.!?])\s+', narrative) if s.strip()
    }
    for m in _PROPER_NOUN.findall(narrative):
        norm = _normalize(m)
        tokens = [_canon(t) for t in norm.split()]
        # Grounded if every word appears in the officer's text.
        if all(t in corpus_tokens for t in tokens):
            continue
        # Phrase made entirely of structural/common words (e.g. headings,
        # "Badge Number", "Incident Report Narrative") → not a fact.
        if all(t in _STOPWORDS for t in tokens):
            continue
        # A lone capitalized word that merely starts a sentence → grammatical.
        if len(tokens) == 1 and tokens[0] in sentence_starts:
            continue
        add('proper_noun', m)

    # ── Numbers / amounts ────────────────────────────────────────────
    for m in _NUMBER.findall(narrative):
        digits = _DIGITS.sub('', m)
        if not digits:
            continue
        if digits not in corpus_digits and _normalize(m) not in corpus:
            add('number', m)

    return flags

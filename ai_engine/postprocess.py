"""
Narrative output post-processing.

Small local models tend to (a) decorate output with Markdown (**bold**, headings)
and (b) echo a signature / officer block at the end — both of which look wrong in
the final document (the template already renders the header + signature). This
strips that packaging deterministically, regardless of model, leaving clean prose.
"""
import re

# Heading/label lines that are pure scaffolding, not narrative content.
_DROP_HEADINGS = {
    'narrative', 'incident report narrative', 'incident narrative',
    'report narrative', 'end of narrative', 'statement of probable cause',
    'affidavit', 'offense description', 'probable cause statement',
}

# Lines that begin an echoed officer/signature block: "Badge Number: ...", etc.
_LABEL_LINE = re.compile(
    r'^\s*(badge(\s*number)?|rank(\s*/?\s*title)?|department(\s*name)?|ori|'
    r'officer|name|division|phone|email|sincerely|respectfully)\s*[:\-]',
    re.I,
)


def _strip_markdown(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # **bold**
    text = re.sub(r'__(.+?)__', r'\1', text)        # __bold__
    text = re.sub(r'\*(.+?)\*', r'\1', text)        # *italic*
    return text.replace('**', '').replace('__', '')


def clean_narrative(text: str, officer: dict | None = None) -> str:
    """Return narrative prose with Markdown and any echoed signature block removed."""
    if not text:
        return text

    text = _strip_markdown(text)
    full_name = (officer or {}).get('full_name', '').strip().lower()

    lines = []
    for raw in text.split('\n'):
        line = re.sub(r'^\s*#{1,6}\s*', '', raw)          # markdown heading markers
        norm = re.sub(r'[^a-z ]', '', line.lower()).strip()
        if norm in _DROP_HEADINGS:                        # drop scaffolding headings
            continue
        lines.append(line)

    # Strip a trailing signature / officer block (and trailing blank lines).
    while lines:
        last = lines[-1].strip()
        low = last.lower()
        is_sig = (
            not last
            or _LABEL_LINE.match(last)
            or (full_name and len(last) < 70 and full_name in low)
        )
        if is_sig:
            lines.pop()
        else:
            break

    out = '\n'.join(lines).strip()
    out = re.sub(r'\n{3,}', '\n\n', out)                  # collapse blank runs
    return out

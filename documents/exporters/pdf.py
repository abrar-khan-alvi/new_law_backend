"""ReportLab PDF exporters — one template per doc_type."""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle('LeTitle', parent=_styles['Title'], fontSize=16, alignment=TA_CENTER)
_H = ParagraphStyle('LeHeading', parent=_styles['Heading2'], fontSize=12, spaceBefore=12)
_BODY = ParagraphStyle('LeBody', parent=_styles['BodyText'], fontSize=10, leading=14)
_SMALL = ParagraphStyle('LeSmall', parent=_styles['BodyText'], fontSize=8, textColor=colors.grey)


def _p(text, style=_BODY):
    return Paragraph((text or '').replace('\n', '<br/>'), style)


def _narrative_paragraphs(narrative):
    blocks = [b.strip() for b in (narrative or '').split('\n\n') if b.strip()]
    return [_p(b) for b in blocks] or [_p('(no narrative)')]


def _kv_table(rows):
    """Two-column label/value table."""
    data = [[_p(f'<b>{k}</b>', _BODY), _p(str(v), _BODY)] for k, v in rows]
    t = Table(data, colWidths=[1.8 * inch, 4.7 * inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ]))
    return t


def _header(officer):
    dept = officer.get('department_name') or 'Law Enforcement Agency'
    bits = [officer.get('department_address'), officer.get('department_state')]
    sub = ' · '.join(b for b in bits if b)
    flow = [_p(f'<b>{dept}</b>', _TITLE)]
    if sub:
        flow.append(_p(sub, ParagraphStyle('c', parent=_SMALL, alignment=TA_CENTER)))
    flow.append(Spacer(1, 8))
    return flow


def _sig_block(officer):
    return [
        Spacer(1, 24),
        _p('_______________________________'),
        _p(f"{officer.get('full_name', '')}, {officer.get('rank', '')}"),
        _p(f"Badge: {officer.get('badge_number', '')}  ORI: {officer.get('ori', '')}", _SMALL),
    ]


# ── Incident report ──────────────────────────────────────────────────
def _incident(form_data, narrative, officer):
    inc = form_data.get('incident', {})
    story = _header(officer)
    story += [_p('INCIDENT REPORT', _TITLE),
              _p(f"Case #: {form_data.get('case_number', '')}",
                 ParagraphStyle('c', parent=_BODY, alignment=TA_CENTER)),
              Spacer(1, 8)]
    story.append(_kv_table([
        ('Categories', ', '.join(inc.get('categories', [])) or '-'),
        ('Date / Time', f"{inc.get('date', '-')} {inc.get('time', '')}"),
        ('Location', inc.get('location', '-')),
        ('Urgency', inc.get('urgency', '-')),
    ]))

    parties = form_data.get('involved_parties', [])
    if parties:
        story += [_p('Persons Involved', _H)]
        rows = [[_p('<b>Role</b>'), _p('<b>Name</b>'), _p('<b>Contact</b>')]]
        for x in parties:
            rows.append([_p(x.get('role', '')), _p(x.get('full_name', '')),
                         _p(x.get('phone') or x.get('email') or '')])
        t = Table(rows, colWidths=[1.3 * inch, 2.7 * inch, 2.5 * inch])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)

    story += [_p('Narrative', _H)] + _narrative_paragraphs(narrative)
    story += _sig_block(officer)
    return story


# ── Search warrant ───────────────────────────────────────────────────
def _search_warrant(form_data, narrative, officer):
    court = form_data.get('court', {})
    place = form_data.get('place_to_search', {})
    offenses = form_data.get('offenses', [])
    items = form_data.get('items_to_seize', [])

    story = _header(officer)
    story += [_p('SEARCH AND SEIZURE WARRANT', _TITLE), Spacer(1, 6)]
    story.append(_kv_table([
        ('District', court.get('district', '-')),
        ('Case #', form_data.get('case_number', '-')),
        ('Judge', court.get('judge_name', '-')),
    ]))
    story += [_p('Offenses', _H)]
    story += [_p(f"• {o.get('code_section', '')} — {o.get('description', '')}") for o in offenses] or [_p('-')]

    story += [_p('Attachment A — Property to be Searched', _H),
              _p(place.get('description', '-')),
              _p(f"Location: {place.get('address', '-')}")]

    story += [_p('Attachment B — Items to be Seized', _H)]
    story += [_p(f"{chr(97 + i)}. {it}") for i, it in enumerate(items)] or [_p('-')]

    story += [_p('Affidavit — Statement of Probable Cause', _H)] + _narrative_paragraphs(narrative)
    story += _sig_block(officer)
    return story


# ── Arrest warrant ───────────────────────────────────────────────────
def _arrest_warrant(form_data, narrative, officer):
    court = form_data.get('court', {})
    defendant = form_data.get('defendant', {})
    offense = form_data.get('offense', {})
    ident = form_data.get('identifiers', {})

    story = _header(officer)
    story += [_p('ARREST WARRANT', _TITLE), Spacer(1, 6)]
    story.append(_kv_table([
        ('District', court.get('district', '-')),
        ('Case #', form_data.get('case_number', '-')),
        ('Defendant', defendant.get('full_name', '-')),
        ('Charging document', form_data.get('charging_document', '-')),
        ('Offense', f"{offense.get('code_section', '')} — {offense.get('brief_description', '')}"),
    ]))

    story += [_p('Defendant Identifiers (Not for Public Disclosure)', _H)]
    story.append(_kv_table([
        ('Aliases', ', '.join(ident.get('aliases', [])) or '-'),
        ('DOB', ident.get('date_of_birth', '-')),
        ('Sex / Race', f"{ident.get('sex', '-')} / {ident.get('race', '-')}"),
        ('Height / Weight', f"{ident.get('height', '-')} / {ident.get('weight', '-')}"),
        ('Last known residence', ident.get('last_known_residence', '-')),
        ('Vehicle', ident.get('vehicle_description', '-')),
    ]))

    if narrative:
        story += [_p('Supporting Affidavit', _H)] + _narrative_paragraphs(narrative)
    story += _sig_block(officer)
    return story


_BUILDERS = {
    'incident_report': _incident,
    'search_warrant': _search_warrant,
    'arrest_warrant': _arrest_warrant,
}


def render_pdf(doc_type, form_data, narrative, officer) -> bytes:
    builder = _BUILDERS.get(doc_type)
    if builder is None:
        raise ValueError(f'No PDF template for doc_type {doc_type}')

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
    )
    doc.build(builder(form_data, narrative, officer))
    return buf.getvalue()

"""python-docx DOCX exporters — one template per doc_type."""
import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


def _title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)


def _heading(doc, text):
    doc.add_heading(text, level=2)


def _kv(doc, rows):
    table = doc.add_table(rows=0, cols=2)
    table.style = 'Light List Accent 1'
    for k, v in rows:
        cells = table.add_row().cells
        cells[0].text = str(k)
        cells[1].text = str(v)


def _narrative(doc, narrative):
    blocks = [b.strip() for b in (narrative or '').split('\n\n') if b.strip()]
    for b in (blocks or ['(no narrative)']):
        doc.add_paragraph(b)


def _header(doc, officer):
    _title(doc, officer.get('department_name') or 'Law Enforcement Agency')
    bits = [officer.get('department_address'), officer.get('department_state')]
    sub = ' · '.join(b for b in bits if b)
    if sub:
        p = doc.add_paragraph(sub)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _signature(doc, officer):
    doc.add_paragraph('\n')
    doc.add_paragraph('_______________________________')
    doc.add_paragraph(f"{officer.get('full_name', '')}, {officer.get('rank', '')}")
    doc.add_paragraph(f"Badge: {officer.get('badge_number', '')}  ORI: {officer.get('ori', '')}")


# ── Incident report ──────────────────────────────────────────────────
def _incident(doc, form_data, narrative, officer):
    inc = form_data.get('incident', {})
    _header(doc, officer)
    _title(doc, 'INCIDENT REPORT')
    doc.add_paragraph(f"Case #: {form_data.get('case_number', '')}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    _kv(doc, [
        ('Categories', ', '.join(inc.get('categories', [])) or '-'),
        ('Date / Time', f"{inc.get('date', '-')} {inc.get('time', '')}"),
        ('Location', inc.get('location', '-')),
        ('Urgency', inc.get('urgency', '-')),
    ])
    parties = form_data.get('involved_parties', [])
    if parties:
        _heading(doc, 'Persons Involved')
        table = doc.add_table(rows=1, cols=3)
        table.style = 'Light List Accent 1'
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text, hdr[2].text = 'Role', 'Name', 'Contact'
        for x in parties:
            c = table.add_row().cells
            c[0].text = x.get('role', '')
            c[1].text = x.get('full_name', '')
            c[2].text = x.get('phone') or x.get('email') or ''
    _heading(doc, 'Narrative')
    _narrative(doc, narrative)
    _signature(doc, officer)


# ── Search warrant ───────────────────────────────────────────────────
def _search_warrant(doc, form_data, narrative, officer):
    court = form_data.get('court', {})
    place = form_data.get('place_to_search', {})
    _header(doc, officer)
    _title(doc, 'SEARCH AND SEIZURE WARRANT')
    _kv(doc, [
        ('District', court.get('district', '-')),
        ('Case #', form_data.get('case_number', '-')),
        ('Judge', court.get('judge_name', '-')),
    ])
    _heading(doc, 'Offenses')
    for o in form_data.get('offenses', []):
        doc.add_paragraph(f"{o.get('code_section', '')} — {o.get('description', '')}", style='List Bullet')
    _heading(doc, 'Attachment A — Property to be Searched')
    doc.add_paragraph(place.get('description', '-'))
    doc.add_paragraph(f"Location: {place.get('address', '-')}")
    _heading(doc, 'Attachment B — Items to be Seized')
    for i, it in enumerate(form_data.get('items_to_seize', [])):
        doc.add_paragraph(f"{chr(97 + i)}. {it}")
    _heading(doc, 'Affidavit — Statement of Probable Cause')
    _narrative(doc, narrative)
    _signature(doc, officer)


# ── Arrest warrant ───────────────────────────────────────────────────
def _arrest_warrant(doc, form_data, narrative, officer):
    court = form_data.get('court', {})
    defendant = form_data.get('defendant', {})
    offense = form_data.get('offense', {})
    ident = form_data.get('identifiers', {})
    _header(doc, officer)
    _title(doc, 'ARREST WARRANT')
    _kv(doc, [
        ('District', court.get('district', '-')),
        ('Case #', form_data.get('case_number', '-')),
        ('Defendant', defendant.get('full_name', '-')),
        ('Charging document', form_data.get('charging_document', '-')),
        ('Offense', f"{offense.get('code_section', '')} — {offense.get('brief_description', '')}"),
    ])
    _heading(doc, 'Defendant Identifiers (Not for Public Disclosure)')
    _kv(doc, [
        ('Aliases', ', '.join(ident.get('aliases', [])) or '-'),
        ('DOB', ident.get('date_of_birth', '-')),
        ('Sex / Race', f"{ident.get('sex', '-')} / {ident.get('race', '-')}"),
        ('Height / Weight', f"{ident.get('height', '-')} / {ident.get('weight', '-')}"),
        ('Last known residence', ident.get('last_known_residence', '-')),
        ('Vehicle', ident.get('vehicle_description', '-')),
    ])
    if narrative:
        _heading(doc, 'Supporting Affidavit')
        _narrative(doc, narrative)
    _signature(doc, officer)


_BUILDERS = {
    'incident_report': _incident,
    'search_warrant': _search_warrant,
    'arrest_warrant': _arrest_warrant,
}


def render_docx(doc_type, form_data, narrative, officer) -> io.BytesIO:
    builder = _BUILDERS.get(doc_type)
    if builder is None:
        raise ValueError(f'No DOCX template for doc_type {doc_type}')
    doc = Document()
    builder(doc, form_data, narrative, officer)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

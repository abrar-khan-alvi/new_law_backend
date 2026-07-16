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
    facts = form_data.get('facts', {})
    parties = form_data.get('involved_parties', [])
    prop = form_data.get('property_items', [])
    notif = form_data.get('notifications', {})

    # Header
    _title(doc, officer.get("department_name") or "Smyrna Police Department")
    _title(doc, "INCIDENT/INVESTIGATION REPORT")
    p_case = doc.add_paragraph()
    p_case.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_case.add_run(f"Case #: {form_data.get('case_number') or '-'}\n").bold = True
    
    # 1. Incident Details
    _heading(doc, "1. Case Information")
    reported_dt = f"{inc.get('reported_date') or inc.get('date', '')} {inc.get('reported_time') or inc.get('time', '')}".strip()
    secure_dt = f"{inc.get('date', '')} {inc.get('time', '')}".strip()
    _kv(doc, [
        ('ORI', officer.get('ori') or 'GA 0330400'),
        ('Date / Time Reported', reported_dt),
        ('Location of Incident', inc.get('location', '-')),
        ('Premise Type', inc.get('premise_type') or 'Hotel/motel/etc.'),
        ('Last Known Secure', secure_dt)
    ])

    # 2. Crimes
    _heading(doc, "2. Offense Details")
    categories = inc.get("categories", []) or ["General Information / Incident"]
    crime_rows = []
    for idx, c_name in enumerate(categories):
        weapon = notif.get("weapon_detail") if notif.get("weapon_involved") else "None"
        crime_rows.append((f"Offense #{idx+1}", c_name))
        crime_rows.append((f"  Weapon / Tools", weapon or "None"))
    _kv(doc, crime_rows)

    # 3. MO Block
    _heading(doc, "3. MO (Modus Operandi)")
    doc.add_paragraph(facts.get('how') or 'N/A')

    # 4. Involved Parties (Victims and Others)
    victims = [p for p in parties if p.get('role') == 'victim']
    others = [p for p in parties if p.get('role') != 'victim']
    
    if victims:
        _heading(doc, "4. Victim Information")
        for idx, v in enumerate(victims):
            dob_val = v.get('dob') or '-'
            _kv(doc, [
                (f"Victim V{idx+1} Name", v.get('full_name', '-')),
                ("DOB", dob_val),
                ("Race / Sex", f"{v.get('race') or 'U'} / {v.get('sex') or 'U'}"),
                ("Resident Status", "Resident" if v.get('address') else "Non-Resident"),
                ("Home Address", v.get('address') or '-'),
                ("Contact Phone", v.get('phone') or '-'),
                ("Email", v.get('email') or '-')
            ])

    if others:
        _heading(doc, "5. Other Involved Parties")
        for idx, o in enumerate(others):
            role_code = "Suspect" if o.get('role') == 'suspect' or o.get('role') == 'alleged' else ("Witness" if o.get('role') == 'witness' else "Other Involved")
            _kv(doc, [
                (f"Party #{idx+1} ({role_code})", o.get('full_name', '-')),
                ("DOB", o.get('dob') or '-'),
                ("Race / Sex", f"{o.get('race') or 'U'} / {o.get('sex') or 'U'}"),
                ("Resident Status", "Resident" if o.get('address') else "Non-Resident"),
                ("Home Address", o.get('address') or '-'),
                ("Contact Phone", o.get('phone') or '-')
            ])

    # 5. Property Items
    prop_items = [p for p in prop if p.get('type') != 'vehicle']
    if prop_items:
        _heading(doc, "6. Property Items")
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Light List Accent 1'
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = 'Status', 'Description', 'Value', 'Serial Number'
        for p_item in prop_items:
            cells = table.add_row().cells
            cells[0].text = p_item.get('status', '')
            cells[1].text = p_item.get('type', '')
            cells[2].text = f"${p_item.get('value')}" if p_item.get('value') else "-"
            cells[3].text = p_item.get('serial_or_tag', '-')

    # 6. Confidentiality Banner
    doc.add_paragraph("\n")
    p_warn = doc.add_paragraph()
    p_warn.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_warn = p_warn.add_run("THE INFORMATION BELOW IS CONFIDENTIAL - FOR USE BY AUTHORIZED PERSONNEL ONLY")
    run_warn.bold = True
    
    # 7. Narrative
    _heading(doc, "Reporting Officer Narrative")
    _narrative(doc, narrative)
    
    # 8. Signatures
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

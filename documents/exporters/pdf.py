"""ReportLab PDF exporters — one template per doc_type."""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
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


def _seal_flowable(officer):
    """Fetch and embed the agency seal image; never fail generation over it."""
    key = officer.get('agency_seal_key')
    if not key:
        return None
    try:
        from reportlab.platypus import Image

        from utils.storage import get_upload_bytes
        data = get_upload_bytes(key)
        if not data:
            return None
        img = Image(io.BytesIO(data), width=0.75 * inch, height=0.75 * inch)
        img.hAlign = 'CENTER'
        return img
    except Exception:  # noqa: BLE001 — cosmetic only, never block document generation
        return None


def _header(officer):
    if officer.get('agency_name'):
        state = officer.get('agency_state') or '_______________________'
        county = officer.get('agency_county') or '_____________________'
        court = officer.get('agency_court_caption') or officer.get('agency_court_name') or '__________________ COURT'
        agency = officer.get('agency_name') or '_______________________'
        district = officer.get('agency_judicial_district')
        division = officer.get('agency_division')

        centered = ParagraphStyle('hjc', parent=_BODY, alignment=TA_CENTER)
        flow = []
        seal = _seal_flowable(officer)
        if seal:
            flow += [seal, Spacer(1, 4)]
        flow += [
            _p(f"STATE OF: {state.upper()}", centered),
            _p(f"COUNTY OF: {county.upper()}", centered),
            _p(f"IN THE {court.upper()}", centered),
        ]
        if district:
            flow.append(_p(f"JUDICIAL DISTRICT: {district.upper()}", centered))
        if division:
            flow.append(_p(f"DIVISION: {division.upper()}", centered))
        flow += [
            _p(f"AGENCY: {agency.upper()}", centered),
            Spacer(1, 16),
        ]
        return flow
    else:
        dept = officer.get('department_name') or 'Law Enforcement Agency'
        bits = [officer.get('department_address'), officer.get('department_state')]
        sub = ' · '.join(b for b in bits if b)
        flow = [_p(f'<b>{dept}</b>', _TITLE)]
        if sub:
            flow.append(_p(sub, ParagraphStyle('c', parent=_SMALL, alignment=TA_CENTER)))
        flow.append(Spacer(1, 8))
        return flow


_BANNER_LABELS = {
    'pending_supervisor': 'DRAFT — PENDING SUPERVISOR REVIEW',
    'pending_prosecutor': 'DRAFT — PENDING PROSECUTOR REVIEW',
    'rejected': 'DRAFT — REVIEW REJECTED, NOT APPROVED FOR FILING',
}


def _draft_banner(doc_meta):
    """"Generate a clean draft for supervisor or prosecutor review before
    judicial submission" — a visible banner while review is outstanding."""
    if not doc_meta:
        return []
    label = _BANNER_LABELS.get(doc_meta.get('review_status'))
    if not label:
        return []
    banner_style = ParagraphStyle(
        'draft', parent=_BODY, alignment=TA_CENTER, textColor=colors.red, fontName='Helvetica-Bold',
    )
    return [_p(label, banner_style), Spacer(1, 10)]


def _sig_block(officer, doc_meta=None):
    doc_meta = doc_meta or {}
    signature_name = doc_meta.get('signature_name')
    signed_at = doc_meta.get('signed_at')
    if signature_name and signed_at:
        return [
            Spacer(1, 24),
            _p(f"/s/ {signature_name}"),
            _p(f"{officer.get('full_name', '')}, {officer.get('rank', '')}"),
            _p(f"Badge: {officer.get('badge_number', '')}  ORI: {officer.get('ori', '')}", _SMALL),
            _p(f"Electronically signed on {signed_at}", _SMALL),
        ]
    return [
        Spacer(1, 24),
        _p('_______________________________'),
        _p(f"{officer.get('full_name', '')}, {officer.get('rank', '')}"),
        _p(f"Badge: {officer.get('badge_number', '')}  ORI: {officer.get('ori', '')}", _SMALL),
    ]


# ── Incident report ──────────────────────────────────────────────────
_LABEL = ParagraphStyle('SmyrnaLabel', parent=_styles['BodyText'], fontSize=6, leading=7, textColor=colors.HexColor('#333333'))
_VALUE = ParagraphStyle('SmyrnaValue', parent=_styles['BodyText'], fontSize=8, leading=9, textColor=colors.black, fontName='Helvetica-Bold')

def _c(label, value):
    val_str = str(value) if value is not None and str(value).strip() != '' else '-'
    return [
        Paragraph(label, _LABEL),
        Paragraph(val_str, _VALUE)
    ]

def _p_small(text):
    return Paragraph(str(text or ''), ParagraphStyle('ps', parent=_styles['BodyText'], fontSize=8, leading=9))

_GRID_STYLE = TableStyle([
    ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ('TOPPADDING', (0, 0), (-1, -1), 2),
    ('LEFTPADDING', (0, 0), (-1, -1), 3),
    ('RIGHTPADDING', (0, 0), (-1, -1), 3),
])


# ── Incident report ──────────────────────────────────────────────────
def _incident(form_data, narrative, officer):
    inc = form_data.get('incident', {})
    facts = form_data.get('facts', {})
    parties = form_data.get('involved_parties', [])
    prop = form_data.get('property_items', [])
    notif = form_data.get('notifications', {})

    story = []

    # 1. Header Grid
    case_no = form_data.get('case_number') or '-'
    reported_dt = f"{inc.get('reported_date') or inc.get('date', '')} {inc.get('reported_time') or inc.get('time', '')}".strip()
    secure_dt = f"{inc.get('date', '')} {inc.get('time', '')}".strip()
    
    header_data = [
        [
            _c("Agency Name", officer.get("department_name") or "(department not set)"),
            Paragraph("<font size=11><b>INCIDENT/INVESTIGATION<br/>REPORT</b></font>", ParagraphStyle('hc', parent=_TITLE, leading=12)),
            _c("Case#", case_no)
        ],
        [
            _c("ORI", officer.get("ori") or "(ORI not set)"),
            "",
            _c("Date / Time Reported", reported_dt)
        ],
        [
            _c("Location of Incident", inc.get("location") or "-"),
            _c("Gang Relat / Premise Type / Beat", f"NO / {inc.get('premise_type') or 'Hotel/motel/etc.'} / D"),
            _c("Last Known Secure / At Found", f"{secure_dt} / {secure_dt}")
        ]
    ]
    
    t_header = Table(header_data, colWidths=[3.0 * inch, 2.3 * inch, 2.2 * inch])
    t_header.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (1, 0), (1, 1)), # Span INCIDENT REPORT title
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (1, 0), (1, 1), 'CENTER'),
        ('VALIGN', (1, 0), (1, 1), 'MIDDLE'),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 4))

    # 2. Crime Incident(s) Grid
    categories = inc.get("categories", [])
    if not categories:
        categories = ["General Information / Incident"]
        
    crime_rows = []
    for idx in range(3):
        crime_name = categories[idx] if idx < len(categories) else ""
        num_str = f"#{idx + 1}"
        weapon = notif.get("weapon_detail") if notif.get("weapon_involved") else "None"
        if not crime_name and idx > 0:
            crime_rows.append([
                _c(f"#{idx + 1} Crime Incident", ""),
                _c("Weapon / Tools", ""),
                _c("Activity / Entry / Exit / Security", "")
            ])
        else:
            crime_rows.append([
                _c(f"{num_str} Crime Incident(s)", crime_name),
                _c("Weapon / Tools", weapon or "None"),
                _c("Activity / Entry / Exit / Security", "N / None / None / None")
            ])
            
    t_crimes = Table(crime_rows, colWidths=[3.5 * inch, 2.0 * inch, 2.0 * inch])
    t_crimes.setStyle(_GRID_STYLE)
    story.append(t_crimes)
    story.append(Spacer(1, 4))

    # 3. MO Block
    mo_val = facts.get("how") or "N/A"
    t_mo = Table([[_c("MO (Modus Operandi)", mo_val)]], colWidths=[7.5 * inch])
    t_mo.setStyle(_GRID_STYLE)
    story.append(t_mo)
    story.append(Spacer(1, 4))

    # 4. Victim(s) Grid (V1)
    victims = [p for p in parties if p.get('role') == 'victim']
    v = victims[0] if victims else {}
    
    dob_val = v.get('dob') or '-'
    age_val = '-'
    if v.get('dob') and '-' in v['dob']:
        try:
            from datetime import datetime
            birth = datetime.strptime(v['dob'], '%Y-%m-%d')
            age_val = str(datetime.now().year - birth.year)
        except Exception:
            pass
            
    veh = {}
    for p_item in prop:
        if p_item.get('type') == 'vehicle':
            veh = p_item
            break
            
    victim_data = [
        [
            _c("# of Victims", str(max(1, len(victims)))),
            _c("Type", "INDIVIDUAL (NON LE)"),
            _c("Injury", form_data.get('injuries', {}).get('description') or "None"),
            _c("Domestic", "N")
        ],
        [
            _c("V1 Victim/Business Name (Last, First, Middle)", v.get('full_name') or "-"),
            _c("DOB", dob_val),
            _c("Age / Race / Sex", f"{age_val} / {v.get('race') or 'U'} / {v.get('sex') or 'M'}"),
            _c("Relationship / Resident Status", f"INR / {v.get('address') and 'Resident' or 'Non-Resident'}")
        ],
        [
            _c("Home Address", v.get('address') or "-"),
            _c("Email", v.get('email') or "-"),
            _c("Home Phone / Mobile", f"{v.get('phone') or '-'} / {v.get('phone') or '-'}")
        ],
        [
            _c("Employer Name/Address", "-"),
            _c("Business Phone", "-"),
            _c("Vehicle Descriptors: VYR / Make / Model / Style / Color / VIN",
               f"{veh.get('year') or '-'} / {veh.get('make') or '-'} / {veh.get('model') or '-'} / - / {veh.get('color') or '-'} / {veh.get('serial_or_tag') or '-'}")
        ]
    ]
    t_victim = Table(victim_data, colWidths=[2.5 * inch, 1.2 * inch, 1.8 * inch, 2.0 * inch])
    t_victim.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (2, 2), (3, 2)),
        ('SPAN', (2, 3), (3, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_victim)
    story.append(Spacer(1, 4))

    # 5. Others Involved (IO / WI / RP)
    others = [p for p in parties if p.get('role') != 'victim']
    
    other_rows = []
    for idx in range(2):
        o = others[idx] if idx < len(others) else {}
        role_code = "IO" if o.get('role') == 'suspect' or o.get('role') == 'alleged' else ("WI" if o.get('role') == 'witness' else "IO")
        dob_o = o.get('dob') or '-'
        if not o and idx > 0:
            other_rows.append([
                _c("Type", ""),
                _c("Code / Name (Last, First, Middle)", ""),
                _c("DOB / Age / Race / Sex", ""),
                _c("Relationship / Resident Status", "")
            ])
            other_rows.append([
                _c("Home Address", ""),
                _c("Email", ""),
                _c("Phone / Mobile", "")
            ])
        else:
            other_rows.append([
                _c("Type", "INDIVIDUAL (NON LE)"),
                _c(f"Code / Name (Last, First, Middle)", f"{role_code} - {o.get('full_name') or '-'}" if o else "-"),
                _c("DOB / Age / Race / Sex", f"{dob_o} / - / {o.get('race') or 'U'} / {o.get('sex') or 'M'}"),
                _c("Relationship / Resident Status", f"None / {o.get('address') and 'Resident' or 'Non-Resident'}")
            ])
            other_rows.append([
                _c("Home Address", o.get('address') or "-"),
                _c("Email", o.get('email') or "-"),
                _c("Phone / Mobile / Employer", f"{o.get('phone') or '-'} / - / -")
            ])
            
    t_others = Table(other_rows, colWidths=[2.2 * inch, 2.2 * inch, 1.5 * inch, 1.6 * inch])
    t_others.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (2, 1), (3, 1)),
        ('SPAN', (2, 3), (3, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_others)
    story.append(Spacer(1, 4))

    # 6. Property Segment
    legend_text = "<font size=5 color='#555555'>1 = None  2 = Burned  3 = Counterfeit / Forged  4 = Damaged / Vandalized  5 = Recovered  6 = Seized  7 = Stolen  8 = Unknown</font>"
    prop_rows = [[Paragraph(legend_text, _LABEL), "", "", "", "", "", "", "", ""]]
    
    headers = ["VI#", "Code", "Status", "Value", "OJ", "QTY", "Property Description", "Make/Model", "Serial Number"]
    prop_rows.append([Paragraph(f"<b>{h}</b>", _LABEL) for h in headers])
    
    prop_items = [p_item for p_item in prop if p_item.get('type') != 'vehicle']
    for idx in range(3):
        p_item = prop_items[idx] if idx < len(prop_items) else {}
        stat_map = {"missing": "7", "stolen": "7", "damaged": "4", "recovered": "5", "seized": "6"}
        code_val = stat_map.get(p_item.get('status'), "1") if p_item else ""
        desc = p_item.get('type', '')
        val = f"${p_item.get('value')}" if p_item.get('value') else ""
        prop_rows.append([
            _p_small("V1" if p_item else ""),
            _p_small(code_val),
            _p_small(p_item.get('status') or ""),
            _p_small(val),
            _p_small("N"),
            _p_small("1" if p_item else ""),
            _p_small(desc),
            _p_small(f"{p_item.get('make') or ''} {p_item.get('model') or ''}".strip()),
            _p_small(p_item.get('serial_or_tag') or "")
        ])
        
    t_prop = Table(prop_rows, colWidths=[0.4 * inch, 0.4 * inch, 0.7 * inch, 0.7 * inch, 0.4 * inch, 0.4 * inch, 2.5 * inch, 1.2 * inch, 1.2 * inch])
    t_prop.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 0), (-1, 0)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 1), (-1, 1), colors.whitesmoke),
    ]))
    story.append(t_prop)
    story.append(Spacer(1, 4))

    # 7. Responding Officers & Case Info
    footer_data = [
        [
            _c("Officer / ID#", f"{officer.get('full_name') or '-'} ({officer.get('badge_number') or '(badge not set)'})"),
            _c("Invest ID# / Name", f"{officer.get('badge_number') or '(badge not set)'} - {officer.get('full_name') or '-'}"),
            _c("Supervisor", "_______________________________")
        ],
        [
            _c("Case Status", "Closed By Investigation"),
            _c("Case Disposition / Date", f"8 / {reported_dt.split(' ')[0] if reported_dt else '-'}"),
            _c("Complainant Signature", "_______________________________")
        ]
    ]
    t_footer = Table(footer_data, colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
    t_footer.setStyle(_GRID_STYLE)
    story.append(t_footer)

    # 8. Extra Name List Page (If needed)
    if len(victims) > 1 or len(others) > 2:
        story.append(PageBreak())
        story.append(Paragraph("<b>Incident Report Additional Name List</b>", _TITLE))
        story.append(Spacer(1, 10))
        extra_parties = victims[1:] + others[2:]
        extra_rows = [[Paragraph(f"<b>Name Code/#</b>", _LABEL), Paragraph(f"<b>Name (Last, First, Middle)</b>", _LABEL), Paragraph(f"<b>DOB / Demographics</b>", _LABEL)]]
        for idx, p in enumerate(extra_parties):
            role_code = "V" if p.get('role') == 'victim' else ("WI" if p.get('role') == 'witness' else "IO")
            extra_rows.append([
                Paragraph(f"{idx+1}) {role_code}", _VALUE),
                Paragraph(p.get('full_name') or '-', _VALUE),
                Paragraph(f"DOB: {p.get('dob') or '-'} | Sex: {p.get('sex') or '-'} | Race: {p.get('race') or '-'}", _BODY)
            ])
        t_extra = Table(extra_rows, colWidths=[1.5 * inch, 3.0 * inch, 3.0 * inch])
        t_extra.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ]))
        story.append(t_extra)

    # 9. Narrative Page
    story.append(PageBreak())
    
    narrative_header = [
        [
            Paragraph("<b>REPORTING OFFICER NARRATIVE</b>", ParagraphStyle('nh', parent=_TITLE, alignment=TA_CENTER, fontSize=12)),
            _c("OCA / Case#", case_no)
        ],
        [
            _c("Victim", v.get('full_name') or '-'),
            _c("Offense", ', '.join(inc.get('categories', [])) or '-')
        ],
        [
            _c("Date / Time Reported", reported_dt),
            ""
        ]
    ]
    t_narr_header = Table(narrative_header, colWidths=[5.0 * inch, 2.5 * inch])
    t_narr_header.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 0), (0, 0)),
        ('SPAN', (1, 1), (1, 2)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_narr_header)
    story.append(Spacer(1, 6))

    confidential_style = ParagraphStyle(
        'Conf', 
        parent=_styles['BodyText'], 
        fontSize=8, 
        fontName='Helvetica-Bold', 
        textColor=colors.black, 
        alignment=TA_CENTER
    )
    conf_table = Table([[Paragraph("THE INFORMATION BELOW IS CONFIDENTIAL - FOR USE BY AUTHORIZED PERSONNEL ONLY", confidential_style)]], colWidths=[7.5 * inch])
    conf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFF00')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(conf_table)
    story.append(Spacer(1, 12))

    story += _narrative_paragraphs(narrative)
    story += _sig_block(officer)

    return story


# ── Search warrant ───────────────────────────────────────────────────
def _search_warrant(form_data, narrative, officer, doc_meta=None):
    court = form_data.get('court', {})
    place = form_data.get('place_to_search', {})
    offenses = form_data.get('offenses', [])
    items = form_data.get('items_to_seize', [])

    story = _header(officer)
    story += _draft_banner(doc_meta)
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
    story += _sig_block(officer, doc_meta)
    return story


# ── Arrest warrant ───────────────────────────────────────────────────
def _arrest_warrant(form_data, narrative, officer, doc_meta=None):
    court = form_data.get('court', {})
    defendant = form_data.get('defendant', {})
    offense = form_data.get('offense', {})
    ident = form_data.get('identifiers', {})

    story = _header(officer)
    story += _draft_banner(doc_meta)
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
    story += _sig_block(officer, doc_meta)
    return story


_BUILDERS = {
    'incident_report': _incident,
    'search_warrant': _search_warrant,
    'arrest_warrant': _arrest_warrant,
}


def render_sw_attachments(form_data, narrative, officer, doc_meta=None) -> bytes:
    """Attachment A (place), Attachment B (items), and the Affidavit — the pages
    that accompany the official AO 93 face form."""
    place = form_data.get('place_to_search', {})
    items = form_data.get('items_to_seize', [])

    story = [
        _p('ATTACHMENT A — Property to be Searched', _TITLE), Spacer(1, 8),
        _p(place.get('description', '-')),
        _p(f"Location: {place.get('address', '-')}"),
        PageBreak(),
        _p('ATTACHMENT B — Items to be Seized', _TITLE), Spacer(1, 8),
    ]
    story += [_p(f"{chr(97 + i)}. {it}") for i, it in enumerate(items)] or [_p('-')]
    story += [
        PageBreak(),
        _p('AFFIDAVIT — Statement of Probable Cause', _TITLE), Spacer(1, 8),
    ] + _narrative_paragraphs(narrative) + _sig_block(officer, doc_meta)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
    )
    doc.build(story)
    return buf.getvalue()


def render_simple_pdf(title, narrative, officer, doc_meta=None) -> bytes:
    """A standalone titled narrative document (e.g. a supporting affidavit)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
    )
    story = _header(officer) + [_p(title, _TITLE), Spacer(1, 8)]
    story += _narrative_paragraphs(narrative)
    story += _sig_block(officer, doc_meta)
    doc.build(story)
    return buf.getvalue()


def render_pdf(doc_type, form_data, narrative, officer, doc_meta=None) -> bytes:
    # The official AO-93/AO-442 federal forms are, by definition, FEDERAL forms —
    # only use them for a federal jurisdiction. A state/municipal agency gets the
    # custom, agency-aware builder below (STATE OF / COUNTY OF / COURT / AGENCY
    # header), never the federal face form (requirement: automatic formatting by
    # jurisdiction level).
    jurisdiction = (
        form_data.get('court', {}).get('jurisdiction_type_override')
        or officer.get('agency_jurisdiction_type')
        or 'state'
    )
    if jurisdiction == 'federal':
        if doc_type == 'arrest_warrant':
            from .ao_forms import fill_arrest_warrant
            return fill_arrest_warrant(form_data, narrative, officer, doc_meta)
        if doc_type == 'search_warrant':
            from .ao_forms import fill_search_warrant
            return fill_search_warrant(form_data, narrative, officer, doc_meta)

    builder = _BUILDERS.get(doc_type)
    if builder is None:
        raise ValueError(f'No PDF template for doc_type {doc_type}')

    buf = io.BytesIO()
    # Incident reports use a custom Smyrna layout with 0.5 margin for max printable width
    margin = 0.5 * inch if doc_type == 'incident_report' else 0.9 * inch
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin,
    )
    if doc_type == 'incident_report':
        doc.build(builder(form_data, narrative, officer))
    else:
        doc.build(builder(form_data, narrative, officer, doc_meta))
    return buf.getvalue()

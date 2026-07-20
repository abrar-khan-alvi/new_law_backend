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
_BODY = ParagraphStyle('LeBody', parent=_styles['BodyText'], fontSize=10, leading=14)
_SMALL = ParagraphStyle('LeSmall', parent=_styles['BodyText'], fontSize=8, textColor=colors.grey)


def _p(text, style=_BODY):
    return Paragraph((text or '').replace('\n', '<br/>'), style)


def _narrative_paragraphs(narrative):
    blocks = [b.strip() for b in (narrative or '').split('\n\n') if b.strip()]
    return [_p(b) for b in blocks] or [_p('(no narrative)')]


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
    """Template cell: tiny label, bold value. Empty boxes show the label only,
    exactly like the printed form (and so an all-labels page stays one page)."""
    val_str = str(value).strip() if value is not None else ''
    if val_str in ('', '-'):
        return [Paragraph(label, _LABEL)]
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


_BAND = ParagraphStyle('SmyrnaBand', parent=_styles['BodyText'], fontSize=5.5, leading=6.5,
                       alignment=TA_CENTER)
_INNER_W = 7.2  # inner grid width (inches); 0.3" is the letter band on the left


def _banded(label, flowables):
    """Vertical letter band on the left of a section, as printed on the form
    (I-N-C-I-D-E-N-T  D-A-T-A …)."""
    letters = '<br/>'.join('&nbsp;' if ch == ' ' else ch for ch in label)
    t = Table([[Paragraph(letters, _BAND), flowables]],
              colWidths=[0.3 * inch, _INNER_W * inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('VALIGN', (1, 0), (1, 0), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t


# ── Incident report ──────────────────────────────────────────────────
def _incident(form_data, narrative, officer):
    inc = form_data.get('incident', {})
    facts = form_data.get('facts', {})
    parties = form_data.get('involved_parties', [])
    prop = form_data.get('property_items', [])
    notif = form_data.get('notifications', {})

    story = []

    # 1. Header Grid — agency/ORI/location | title + gang/premise/beat |
    #    stacked Case# / Date Reported / Last Known Secure / At Found column
    case_no = form_data.get('case_number') or '-'
    reported_dt = f"{inc.get('reported_date') or inc.get('date', '')} {inc.get('reported_time') or inc.get('time', '')}".strip()
    secure_dt = f"{inc.get('date', '')} {inc.get('time', '')}".strip()

    header_data = [
        [
            _c("Agency Name", officer.get("department_name") or "(department not set)"),
            Paragraph("<font size=11><b>INCIDENT/INVESTIGATION<br/>REPORT</b></font>",
                      ParagraphStyle('hc', parent=_TITLE, leading=12)),
            '', '',
            _c("Case#", case_no),
        ],
        [
            _c("ORI", officer.get("ori") or "(ORI not set)"),
            '', '', '',
            _c("Date / Time Reported", reported_dt),
        ],
        [
            _c("Location of Incident", inc.get("location") or "-"),
            _c("Gang Relat", "NO"),
            _c("Premise Type", inc.get('premise_type') or 'Hotel/motel/etc.'),
            _c("Beat/Tract", "D"),
            _c("Last Known Secure", secure_dt),
        ],
        ['', '', '', '', _c("At Found", secure_dt)],
    ]
    t_header = Table(header_data,
                     colWidths=[3.0 * inch, 0.75 * inch, 1.15 * inch, 0.6 * inch, 1.7 * inch])
    t_header.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (1, 0), (3, 1)),   # title block
        ('SPAN', (0, 2), (0, 3)),   # location box is two rows tall
        ('SPAN', (1, 2), (1, 3)),
        ('SPAN', (2, 2), (2, 3)),
        ('SPAN', (3, 2), (3, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (1, 0), (3, 1), 'CENTER'),
        ('VALIGN', (1, 0), (3, 1), 'MIDDLE'),
    ]))
    incident_region = [t_header]

    # 2. Crime Incident(s) Grid — each crime: main row + Entry/Exit/Security sub-row
    categories = inc.get("categories", [])
    if not categories:
        categories = ["General Information / Incident"]

    crime_rows = []
    for idx in range(3):
        crime_name = categories[idx] if idx < len(categories) else ""
        weapon = (notif.get("weapon_detail") if notif.get("weapon_involved") else "None") or "None"
        filled = bool(crime_name)
        crime_rows.append([
            _c(f"#{idx + 1} Crime Incident(s)  (Com)", crime_name),
            _c("Weapon / Tools", weapon if filled else ""),
            '',
            _c("Activity", "N" if filled else ""),
        ])
        crime_rows.append([
            '',
            _c("Entry", "None" if filled else ""),
            _c("Exit", "None" if filled else ""),
            _c("Security", "None" if filled else ""),
        ])
    t_crimes = Table(crime_rows,
                     colWidths=[3.0 * inch, 1.55 * inch, 1.5 * inch, 1.15 * inch])
    crime_style = [
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]
    for pair in range(3):
        crime_style.append(('SPAN', (0, pair * 2), (0, pair * 2 + 1)))   # crime cell 2 rows tall
        crime_style.append(('SPAN', (1, pair * 2), (2, pair * 2)))       # weapon spans two cols
    t_crimes.setStyle(TableStyle(crime_style))
    incident_region.append(t_crimes)
    story.append(_banded('INCIDENT DATA', incident_region))

    # 3. MO Block
    mo_val = facts.get("how") or "N/A"
    t_mo = Table([[_c("MO (Modus Operandi)", mo_val)]], colWidths=[_INNER_W * inch])
    t_mo.setStyle(_GRID_STYLE)
    story.append(_banded('MO', [t_mo]))

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
            
    def _simple_grid(data, widths):
        t = Table(data, colWidths=[w * inch for w in widths])
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        return t

    resident = 'Resident' if v.get('address') else 'Non-Resident'
    victim_tables = [
        _simple_grid([[
            _c("# of Victims", str(max(1, len(victims)))),
            _c("Type", "INDIVIDUAL (NON LE)"),
            _c("Injury", form_data.get('injuries', {}).get('description') or "None"),
            _c("Domestic", "N"),
        ]], [1.3, 1.9, 2.1, 1.9]),
        _simple_grid([[
            _c("V1 Victim/Business Name (Last, First, Middle)", v.get('full_name') or "-"),
            _c("Victim of Crime #", "1"),
            _c("DOB / Age", f"{dob_val} / {age_val}"),
            _c("Race", v.get('race') or 'U'),
            _c("Sex", v.get('sex') or 'U'),
            _c("Relationship To Offender", "INR"),
            _c("Resident Status", resident),
            _c("Military Branch/Status", "-"),
        ]], [2.2, 0.7, 1.0, 0.4, 0.4, 0.9, 0.8, 0.8]),
        _simple_grid([[
            _c("Home Address", v.get('address') or "-"),
            _c("Email", v.get('email') or "-"),
            _c("Home Phone", v.get('phone') or "-"),
        ]], [3.3, 2.0, 1.9]),
        _simple_grid([[
            _c("Employer Name/Address", "-"),
            _c("Business Phone", "-"),
            _c("Mobile Phone", v.get('phone') or "-"),
        ]], [3.3, 2.0, 1.9]),
        _simple_grid([[
            _c("VYR", veh.get('year') or "-"),
            _c("Make", veh.get('make') or "-"),
            _c("Model", veh.get('model') or "-"),
            _c("Style", "-"),
            _c("Color", veh.get('color') or "-"),
            _c("Lic/Lis", "-"),
            _c("VIN", veh.get('serial_or_tag') or "-"),
        ]], [0.7, 1.2, 1.2, 0.9, 0.9, 1.1, 1.2]),
    ]
    story.append(_banded('VICTIM', victim_tables))

    # CODES legend row (template: sits between the victim and others sections)
    t_codes = Table([[Paragraph(
        '<font size=6><b>CODES:</b>   V = Victim (Denote V2, V3)     WI = Witness     '
        'IO = Involved Other     RP = Reporting Person (if other than victim)</font>', _LABEL)]],
        colWidths=[_INNER_W * inch])
    t_codes.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
    ]))

    # 5. Others Involved (IO / WI / RP) — template block per person
    others = [p for p in parties if p.get('role') != 'victim']

    others_tables = [t_codes]
    for idx in range(2):
        o = others[idx] if idx < len(others) else {}
        role_code = "WI" if o.get('role') == 'witness' else "IO"
        others_tables.append(_simple_grid([[
            _c("Type:", "INDIVIDUAL (NON LE)" if o else ""),
            _c("Injury:", ""),
        ]], [3.6, 3.6]))
        others_tables.append(_simple_grid([[
            _c("Code", role_code if o else ""),
            _c("Name (Last, First, Middle)", o.get('full_name') or ("-" if o else "")),
            _c("Victim of Crime #", ""),
            _c("DOB / Age", o.get('dob') or ("-" if o else "")),
            _c("Race", (o.get('race') or 'U') if o else ""),
            _c("Sex", (o.get('sex') or 'U') if o else ""),
            _c("Relationship To Offender", "None" if o else ""),
            _c("Resident Status", ('Resident' if o.get('address') else 'Non-Resident') if o else ""),
        ]], [0.5, 2.1, 0.7, 1.0, 0.4, 0.4, 1.1, 1.0]))
        others_tables.append(_simple_grid([[
            _c("Home Address", o.get('address') or ("-" if o else "")),
            _c("Email", o.get('email') or ("-" if o else "")),
            _c("Home Phone", o.get('phone') or ("-" if o else "")),
        ]], [3.3, 2.0, 1.9]))
        others_tables.append(_simple_grid([[
            _c("Employer Name/Address", "-" if o else ""),
            _c("Business Phone", "-" if o else ""),
            _c("Mobile Phone", o.get('phone') or ("-" if o else "")),
        ]], [3.3, 2.0, 1.9]))
    story.append(_banded('OTHERS INVOLVED', others_tables))

    # 6. Property Segment
    legend_text = "<font size=5 color='#555555'>1 = None  2 = Burned  3 = Counterfeit / Forged  4 = Damaged / Vandalized  5 = Recovered  6 = Seized  7 = Stolen  8 = Unknown</font>"
    prop_rows = [[Paragraph(legend_text, _LABEL), "", "", "", "", "", "", "", ""]]
    
    headers = ["VI#", "Code", "Status", "Value", "OJ", "QTY", "Property Description", "Make/Model", "Serial Number"]
    prop_rows.append([Paragraph(f"<b>{h}</b>", _LABEL) for h in headers])
    
    prop_items = [p_item for p_item in prop if p_item.get('type') != 'vehicle']
    # Template shows a full block of property rows even when mostly empty.
    for idx in range(max(8, len(prop_items))):
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
        
    t_prop = Table(prop_rows, colWidths=[w * inch for w in
                                         [0.35, 0.4, 0.55, 0.6, 0.3, 0.35, 2.35, 1.15, 1.15]])
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
    story.append(_banded('PROPERTY', [t_prop]))

    # 7. Responding Officers & Case Info — Status band on the bottom row
    t_officers = _simple_grid([[
        _c("Officer / ID#", f"{officer.get('full_name') or '-'} ({officer.get('badge_number') or '(badge not set)'})"),
        _c("Invest ID# / Name", f"{officer.get('badge_number') or '(badge not set)'} - {officer.get('full_name') or '-'}"),
        _c("Supervisor", "_______________________________"),
    ]], [2.4, 2.4, 2.4])
    story.append(_banded('', [t_officers]))
    t_status = _simple_grid([[
        _c("Complainant Signature", "_______________________________"),
        _c("Case Status", "Closed By Investigation"),
        _c("Case Disposition / Date", f"8 / {reported_dt.split(' ')[0] if reported_dt else '-'}"),
    ]], [2.4, 2.4, 2.4])
    story.append(_banded('Status', [t_status]))

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

    # 9. Page 2 — drugs / assisting officers / hate-bias (template page 2)
    story.append(PageBreak())
    story.append(Paragraph('<b>INCIDENT/INVESTIGATION REPORT</b>',
                           ParagraphStyle('p2t', parent=_TITLE, fontSize=12)))
    story.append(Paragraph(
        f"<i>{officer.get('department_name') or ''}</i>    Case # {case_no}",
        ParagraphStyle('p2s', parent=_SMALL, alignment=TA_CENTER)))
    story.append(Spacer(1, 4))

    drug_legend = ('<font size=5 color="#555555"><b>Status Codes:</b>  1 = None   2 = Burned   '
                   '3 = Counterfeit / Forged   4 = Damaged / Vandalized   5 = Recovered   '
                   '6 = Seized   7 = Stolen   8 = Unknown</font>')
    drug_headers = ['IBR', 'Status', 'Quantity', 'Type Measure', 'Suspected Type']
    drug_rows = [[Paragraph(drug_legend, _LABEL), '', '', '', '']]
    drug_rows.append([Paragraph(f'<b>{h}</b>', _LABEL) for h in drug_headers])
    drugs = form_data.get('drugs', [])
    for idx in range(max(6, len(drugs))):
        d_item = drugs[idx] if idx < len(drugs) else {}
        drug_rows.append([
            _p_small(d_item.get('ibr', '')),
            _p_small(d_item.get('status', '')),
            _p_small(d_item.get('quantity', '')),
            _p_small(d_item.get('type_measure', '')),
            _p_small(d_item.get('suspected_type', '')),
        ])
    t_drugs = Table(drug_rows, colWidths=[w * inch for w in [0.55, 0.75, 0.95, 1.15, 3.8]])
    t_drugs.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 0), (-1, 0)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 1), (-1, 1), colors.whitesmoke),
    ]))
    story.append(_banded('DRUGS', [t_drugs]))

    assisting = form_data.get('assisting_officers', [])
    if isinstance(assisting, list):
        assisting = ',  '.join(a for a in assisting if a)
    t_assist = Table([
        [_c('Assisting Officers', assisting or '')],
        [_c('Suspect Hate / Bias Motivated:', form_data.get('hate_bias', '') or '')],
    ], colWidths=[_INNER_W * inch])
    t_assist.setStyle(_GRID_STYLE)
    story.append(_banded('', [t_assist]))
    story.append(Spacer(1, 10))

    # 10. Narrative continuation — template style: title, "Narr. (cont.) OCA:",
    #     agency line, then the boxed NARRATIVE section.
    story.append(Paragraph('<b>INCIDENT/INVESTIGATION REPORT</b>',
                           ParagraphStyle('nct', parent=_TITLE, fontSize=12)))
    t_narr_line = Table([[
        _p_small(f"Narr. (cont.)  OCA: {case_no}"),
        Paragraph(f"<i>{officer.get('department_name') or ''}</i>",
                  ParagraphStyle('nca', parent=_SMALL, alignment=TA_CENTER)),
        '',
    ]], colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
    t_narr_line.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_narr_line)

    # A one-cell boxed table can't split across pages (LayoutError on long
    # narratives), so box only the NARRATIVE label and let the text flow.
    t_narr_head = Table([[Paragraph('<font size=7>N A R R A T I V E</font>', _LABEL)]],
                        colWidths=[7.5 * inch])
    t_narr_head.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_narr_head)
    story.append(Spacer(1, 8))
    story += _narrative_paragraphs(narrative)
    story += _sig_block(officer)

    return story


# ── Warrants (non-federal) — the AO 442 / AO 93 template layout drawn with
#    the agency's admin-configured jurisdiction header (requirement #1/#3).
#    Federal agencies get the official AO forms instead (see render_pdf).
_CENTER = ParagraphStyle('LeCenter', parent=_BODY, alignment=TA_CENTER)
_CAPT = ParagraphStyle('LeSigCaption', parent=_SMALL, alignment=TA_CENTER)


def _caption_table(left_lines, case_number):
    """Two-column case caption (parties / matter | Case No.)."""
    left = [_p(line, _CENTER) for line in left_lines]
    t = Table(
        [[left, _p(f"<b>Case No.</b> {case_number or '__________________'}")]],
        colWidths=[3.6 * inch, 3.0 * inch],
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEAFTER', (0, 0), (0, 0), 0.75, colors.black),
        ('LEFTPADDING', (1, 0), (1, 0), 14),
    ]))
    return [t, Spacer(1, 10)]


def _sig_line(left_label, right_caption):
    t = Table([[
        _p(f"{left_label} ____________________" if left_label else ''),
        [_p('_________________________________', _CENTER), _p(f'<i>{right_caption}</i>', _CAPT)],
    ]], colWidths=[3.2 * inch, 3.5 * inch])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    return [Spacer(1, 14), t]


def _checkline(options, selected_key):
    # Standard PDF fonts have no ☐/☒ glyphs — use [X]/[  ] instead.
    return _p('&nbsp;&nbsp;&nbsp;'.join(
        f"[{'X' if key == selected_key else '&nbsp;&nbsp;'}] {label}" for key, label in options))


_CHARGING_DOCS_ROW1 = [
    ('indictment', 'Indictment'),
    ('superseding_indictment', 'Superseding Indictment'),
    ('information', 'Information'),
    ('superseding_information', 'Superseding Information'),
    ('complaint', 'Complaint'),
]
_CHARGING_DOCS_ROW2 = [
    ('probation_violation', 'Probation Violation Petition'),
    ('supervised_release_violation', 'Supervised Release Violation Petition'),
    ('violation_notice', 'Violation Notice'),
    ('court_order', 'Order of the Court'),
]


def _plaintiff_caption(officer):
    state = officer.get('agency_state')
    return f"STATE OF {state.upper()}" if state else 'THE STATE'


def _arrest_warrant(form_data, narrative, officer, doc_meta=None):
    defendant = form_data.get('defendant', {})
    offense = form_data.get('offense', {})
    ident = form_data.get('identifiers', {})
    name = defendant.get('full_name', '')

    story = _header(officer)
    story += _draft_banner(doc_meta)
    story += _caption_table(
        [_plaintiff_caption(officer), 'v.', name or '____________________', '<i>Defendant</i>'],
        form_data.get('case_number'))
    story += [_p('<b>ARREST WARRANT</b>', _TITLE), Spacer(1, 6)]
    story.append(_p('To:&nbsp;&nbsp;&nbsp;&nbsp;Any authorized law enforcement officer'))
    story.append(Spacer(1, 6))
    story.append(_p(
        '<b>YOU ARE COMMANDED</b> to arrest and bring before a judge of this Court without '
        f"unnecessary delay <i>(name of person to be arrested)</i> {name or '____________________'}, "
        'who is accused of an offense or violation based on the following document filed with the court:'))
    story.append(Spacer(1, 4))
    story.append(_checkline(_CHARGING_DOCS_ROW1, form_data.get('charging_document', '')))
    story.append(_checkline(_CHARGING_DOCS_ROW2, form_data.get('charging_document', '')))
    story.append(Spacer(1, 8))
    story.append(_p('This offense is briefly described as follows:'))
    story.append(_p(
        f"{offense.get('code_section', '')}  {offense.get('brief_description', '')}".strip() or '-'))
    story += _sig_line('Date:', 'Issuing officer’s signature')
    story += _sig_line('City and state:', 'Printed name and title')

    return_cell = [
        _p('<b>Return</b>', _CENTER),
        _p('This warrant was received on <i>(date)</i> ______________, and the person was '
           'arrested on <i>(date)</i> ______________ at <i>(city and state)</i> ____________________.'),
    ] + _sig_line('Date:', 'Arresting officer’s signature') + _sig_line('', 'Printed name and title')
    t = Table([[return_cell]], colWidths=[6.7 * inch])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 8)]))
    story += [Spacer(1, 16), t]

    # Page 2 — sealed personal identifiers (template page 2).
    story.append(PageBreak())
    story.append(_p('<b>This second page contains personal identifiers provided for '
                    'law-enforcement use only and therefore should not be filed in court with '
                    'the executed warrant unless under seal.</b>', _CENTER))
    story += [Spacer(1, 6), _p('<i>(Not for Public Disclosure)</i>', _CENTER), Spacer(1, 10)]
    associates = '; '.join(
        f"{a.get('name', '')} ({a.get('relation', '')}) {a.get('phone', '')}".strip()
        for a in ident.get('known_associates', []))
    blank = '_________________________________'
    for label, value in [
        ('Name of defendant/offender', name),
        ('Known aliases', ', '.join(ident.get('aliases', []))),
        ('Last known residence', ident.get('last_known_residence', '')),
        ('Prior addresses to which defendant/offender may still have ties',
         '; '.join(ident.get('prior_addresses', []))),
        ('Last known employment', ident.get('last_known_employment', '')),
        ('Last known telephone numbers', ', '.join(ident.get('phone_numbers', []))),
        ('Place of birth', ident.get('place_of_birth', '')),
        ('Date of birth', ident.get('date_of_birth', '')),
        ('Social Security number', ident.get('ssn', '')),
        ('Height', ident.get('height', '')),
        ('Weight', ident.get('weight', '')),
        ('Sex', ident.get('sex', '')),
        ('Race', ident.get('race', '')),
        ('Hair', ident.get('hair', '')),
        ('Eyes', ident.get('eyes', '')),
        ('Scars, tattoos, other distinguishing marks', ident.get('distinguishing_marks', '')),
        ('History of violence, weapons, drug use', ident.get('history_violence_weapons_drugs', '')),
        ('Known family, friends, and other associates (name, relation, address, phone number)',
         associates),
        ('FBI number', ident.get('fbi_number', '')),
        ('Complete description of auto', ident.get('vehicle_description', '')),
        ('Investigative agency and address', ident.get('investigative_agency', '')),
    ]:
        story.append(_p(f"{label}: {value or blank}"))

    if narrative and narrative.strip():
        story += [PageBreak(), _p('SUPPORTING AFFIDAVIT', _TITLE), Spacer(1, 8)]
        story += _narrative_paragraphs(narrative)
        story += _sig_block(officer, doc_meta)
    return story


def _search_warrant(form_data, narrative, officer, doc_meta=None):
    place = form_data.get('place_to_search', {})
    execution = form_data.get('execution', {})
    court = form_data.get('court', {})
    judge_title = officer.get('agency_judge_title') or 'Judge'
    place_lines = [line for line in [place.get('description'), place.get('address')] if line]

    story = _header(officer)
    story += _draft_banner(doc_meta)
    story += _caption_table(
        ['In the Matter of the Search of'] + (place_lines or ['____________________']),
        form_data.get('case_number'))
    story += [_p('<b>SEARCH AND SEIZURE WARRANT</b>', _TITLE), Spacer(1, 6)]
    story.append(_p('To:&nbsp;&nbsp;&nbsp;&nbsp;Any authorized law enforcement officer'))
    story.append(Spacer(1, 6))

    county = officer.get('agency_county')
    state = officer.get('agency_state')
    locality = ', '.join(x for x in [f"{county} County" if county else '', state] if x) \
        or '____________________'
    story.append(_p(
        'An application by a law enforcement officer or an attorney for the government requests '
        f'the search of the following person or property located in {locality} '
        '<i>(identify the person or describe the property to be searched and give its location)</i>:'))
    story.append(_p('See Attachment A.'))
    story.append(Spacer(1, 8))
    story.append(_p(
        'I find that the affidavit(s), or any recorded testimony, establish probable cause to '
        'search and seize the person or property described above, and that such search will '
        'reveal <i>(identify the person or describe the property to be seized)</i>:'))
    story.append(_p('See Attachment B.'))
    story.append(Spacer(1, 8))

    story.append(_p(
        '<b>YOU ARE COMMANDED</b> to execute this warrant on or before '
        f"{execution.get('execute_by_date') or '____________'} <i>(not to exceed 14 days)</i>"))
    anytime = execution.get('time_window') == 'anytime'
    story.append(_checkline([
        ('daytime', 'in the daytime 6:00 a.m. to 10:00 p.m.'),
        ('anytime', 'at any time in the day or night because good cause has been established.'),
    ], 'anytime' if anytime else 'daytime'))
    story.append(Spacer(1, 8))
    story.append(_p(
        'Unless delayed notice is authorized below, you must give a copy of the warrant and a '
        'receipt for the property taken to the person from whom, or from whose premises, the '
        'property was taken, or leave the copy and receipt at the place where the property was taken.'))
    story.append(_p(
        'The officer executing this warrant, or an officer present during the execution of the '
        'warrant, must prepare an inventory as required by law and promptly return this warrant '
        f"and inventory to {court.get('judge_name') or '____________________'} <i>({judge_title})</i>."))
    story += _sig_line('Date and time issued:', 'Judge’s signature')
    story += _sig_line('City and state:', 'Printed name and title')

    # Page 2 — Return / Certification (template page 2).
    story.append(PageBreak())
    return_cell = [_p('<b>Return</b>', _CENTER)]
    for label, value in [
        ('Case No.', form_data.get('case_number', '')),
        ('Date and time warrant executed', ''),
        ('Copy of warrant and inventory left with', ''),
        ('Inventory made in the presence of', ''),
        ('Inventory of the property taken and name of any person(s) seized', ''),
    ]:
        return_cell.append(_p(f"{label}: {value or '____________________'}"))
    return_cell += [
        Spacer(1, 10),
        _p('<b>Certification</b>', _CENTER),
        _p('I declare under penalty of perjury that this inventory is correct and was returned '
           'along with the original warrant to the designated judge.'),
    ]
    return_cell += _sig_line('Date:', 'Executing officer’s signature')
    return_cell += _sig_line('', 'Printed name and title')
    t = Table([[return_cell]], colWidths=[6.7 * inch])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 8)]))
    story.append(t)

    # Attachments + affidavit referenced by the face form.
    story += [
        PageBreak(), _p('ATTACHMENT A — Property to be Searched', _TITLE), Spacer(1, 8),
        _p(place.get('description', '-')),
        _p(f"Location: {place.get('address', '-')}"),
        PageBreak(), _p('ATTACHMENT B — Items to be Seized', _TITLE), Spacer(1, 8),
    ]
    story += [_p(f"{chr(97 + i)}. {it}") for i, it in enumerate(form_data.get('items_to_seize', []))] \
        or [_p('-')]
    story += [PageBreak(), _p('AFFIDAVIT — Statement of Probable Cause', _TITLE), Spacer(1, 8)]
    story += _narrative_paragraphs(narrative)
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

    story = _draft_banner(doc_meta) + [
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
    story = _header(officer) + _draft_banner(doc_meta) + [_p(title, _TITLE), Spacer(1, 8)]
    story += _narrative_paragraphs(narrative)
    story += _sig_block(officer, doc_meta)
    doc.build(story)
    return buf.getvalue()


def render_pdf(doc_type, form_data, narrative, officer, doc_meta=None) -> bytes:
    # Warrants follow the AO 442 / AO 93 template layout (docs/…/Arrest Warrant
    # Template.pdf, Search Warrant Template.pdf). Federal agencies fill the
    # official forms themselves; state/municipal agencies get the same layout
    # drawn with their admin-configured jurisdiction header instead of the
    # hard-coded federal caption (requirements #1 and #3).
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
        def _page_num(canvas, _doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 7)
            canvas.drawRightString(letter[0] - 0.5 * inch, 0.3 * inch,
                                   f"Page {canvas.getPageNumber()}")
            canvas.restoreState()
        doc.build(builder(form_data, narrative, officer),
                  onFirstPage=_page_num, onLaterPages=_page_num)
    else:
        doc.build(builder(form_data, narrative, officer, doc_meta))
    return buf.getvalue()

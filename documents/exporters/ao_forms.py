"""Fill official U.S. court warrant forms and append supporting pages."""
import io
import os

import fitz

FORMS_DIR = os.path.join(os.path.dirname(__file__), 'forms')
AO442_PATH = os.path.join(FORMS_DIR, 'ao442_arrest_warrant.pdf')
AO93_PATH = os.path.join(FORMS_DIR, 'ao93_search_warrant.pdf')

CHARGING_ON_STATE = {
    'indictment': '5', 'superseding_indictment': '0', 'information': '1',
    'superseding_information': '2', 'complaint': '6',
    'probation_violation': '7', 'supervised_release_violation': '3',
    'violation_notice': '4', 'court_order': '8',
}


def _text_map(form_data, officer):
    court = form_data.get('court', {})
    defendant = form_data.get('defendant', {})
    offense = form_data.get('offense', {})
    identifiers = form_data.get('identifiers', {})
    name = defendant.get('full_name', '')
    associates = '; '.join(
        f"{item.get('name', '')} ({item.get('relation', '')}) {item.get('phone', '')}".strip()
        for item in identifiers.get('known_associates', [])
    )
    return {
        'Dist.Info': (court.get('district') or officer.get('agency_judicial_district')
                      or officer.get('agency_state') or ''),
        'Defendant1': name, 'Defendant2': name,
        'Case number': form_data.get('case_number', ''),
        'Offense Description': (
            f"{offense.get('code_section', '')}  {offense.get('brief_description', '')}".strip()
        ),
        'Defendant3': name,
        'Aliases': ', '.join(identifiers.get('aliases', [])),
        'Last Known residence': identifiers.get('last_known_residence', ''),
        'Prior addresses1': '; '.join(identifiers.get('prior_addresses', [])),
        'Last Known Employment': identifiers.get('last_known_employment', ''),
        'Last known telephone numbers': ', '.join(identifiers.get('phone_numbers', [])),
        'Place of birth': identifiers.get('place_of_birth', ''),
        'DOB': identifiers.get('date_of_birth', ''),
        'Social Security number': identifiers.get('ssn', ''),
        'Height': identifiers.get('height', ''), 'Weight': identifiers.get('weight', ''),
        'Sex': identifiers.get('sex', ''), 'Race': identifiers.get('race', ''),
        'Hair': identifiers.get('hair', ''), 'Eyes': identifiers.get('eyes', ''),
        'Distinguishing marks1': identifiers.get('distinguishing_marks', ''),
        'History': identifiers.get('history_violence_weapons_drugs', ''),
        'Family1': associates, 'FBI number': identifiers.get('fbi_number', ''),
        'Auto1': identifiers.get('vehicle_description', ''),
        'Agency address': identifiers.get('investigative_agency', ''),
    }


def _add_watermark(doc):
    text = 'UNVERIFIED ACCOUNT - TEST USE ONLY'
    font_size = 20
    text_width = fitz.get_text_length(text, fontname='helv', fontsize=font_size)
    for page in doc:
        page.insert_text(
            fitz.Point(max(36, (page.rect.width - text_width) / 2), page.rect.height / 2),
            text, color=(1, 0, 0), fontsize=font_size, fontname='helv',
            rotate=0, fill_opacity=0.25, overlay=True,
        )


def fill_arrest_warrant(form_data, narrative, officer, doc_meta=None, is_test_export=False) -> bytes:
    text_map = _text_map(form_data, officer)
    charge_state = CHARGING_ON_STATE.get(form_data.get('charging_document', ''))
    doc = fitz.open(AO442_PATH)
    for page in doc:
        for widget in (page.widgets() or []):
            name = widget.field_name
            if name in text_map and text_map[name]:
                widget.field_value = str(text_map[name])
                widget.update()
            elif name == 'Document' and charge_state:
                on_states = [s for s in widget.button_states().get('normal', []) if s != 'Off']
                if on_states and on_states[0] == charge_state:
                    widget.field_value = charge_state
                    widget.update()

    if narrative and narrative.strip():
        from .pdf import render_simple_pdf
        affidavit_bytes = render_simple_pdf('SUPPORTING AFFIDAVIT', narrative, officer, doc_meta)
        affidavit = fitz.open(stream=affidavit_bytes, filetype='pdf')
        doc.insert_pdf(affidavit)
        affidavit.close()
    if is_test_export:
        _add_watermark(doc)
    output = io.BytesIO(doc.tobytes())
    doc.close()
    return output.getvalue()


def fill_search_warrant(form_data, narrative, officer, doc_meta=None, is_test_export=False) -> bytes:
    court = form_data.get('court', {})
    district = (court.get('district') or officer.get('agency_judicial_district')
                or officer.get('agency_state') or '')
    prefix, separator, state = district.partition(' District of ')
    if not separator:
        prefix, state = '', district.removeprefix('District of ').strip()
    execution = form_data.get('execution', {})
    place = form_data.get('place_to_search', {})
    doc = fitz.open(AO93_PATH)
    page = doc[0]

    def put(x, y, value, size=9):
        if value:
            page.insert_text((x, y), str(value), fontsize=size)

    put(232, 119, prefix)
    put(335, 119, state)
    caption = '\n'.join(value for value in (place.get('description'), place.get('address')) if value)
    for size in (9, 8, 7, 6):
        if not caption or page.insert_textbox(fitz.Rect(35, 176, 295, 245), caption, fontsize=size) >= 0:
            break
    put(240, 284, prefix)
    put(415, 284, state)
    put(372, 172, form_data.get('case_number', ''))
    put(57, 312, 'See Attachment A.')
    put(57, 410, 'See Attachment B.')
    put(350, 497, execution.get('execute_by_date', ''))
    put(242 if execution.get('time_window') == 'anytime' else 45, 512, 'X', 11)
    put(430, 593, court.get('judge_name', ''))

    from .pdf import render_sw_attachments
    extra_bytes = render_sw_attachments(form_data, narrative, officer, doc_meta)
    extra = fitz.open(stream=extra_bytes, filetype='pdf')
    doc.insert_pdf(extra)
    extra.close()
    if is_test_export:
        _add_watermark(doc)
    output = io.BytesIO(doc.tobytes())
    doc.close()
    return output.getvalue()

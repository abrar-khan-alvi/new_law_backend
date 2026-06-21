"""
Fill official fillable U.S. court forms (AcroForm field-fill) for court-exact output.

AO 442 (Arrest Warrant) is a fillable AcroForm — we set its named fields directly,
check the correct charging-document radio, fill the page-2 identifiers, and append
a supporting affidavit (if a narrative is provided) as extra pages.
"""
import io
import os

import fitz  # PyMuPDF

FORMS_DIR = os.path.join(os.path.dirname(__file__), 'forms')
AO442_PATH = os.path.join(FORMS_DIR, 'ao442_arrest_warrant.pdf')
AO93_PATH = os.path.join(FORMS_DIR, 'ao93_search_warrant.pdf')

# charging_document value -> radio "Document" on-state (mapped by field position)
CHARGING_ON_STATE = {
    'indictment': '5',
    'superseding_indictment': '0',
    'information': '1',
    'superseding_information': '2',
    'complaint': '6',
    'probation_violation': '7',
    'supervised_release_violation': '3',
    'violation_notice': '4',
    'court_order': '8',
}


def _text_map(form_data):
    court = form_data.get('court', {})
    defn = form_data.get('defendant', {})
    off = form_data.get('offense', {})
    ident = form_data.get('identifiers', {})
    name = defn.get('full_name', '')
    associates = '; '.join(
        f"{a.get('name', '')} ({a.get('relation', '')}) {a.get('phone', '')}".strip()
        for a in ident.get('known_associates', [])
    )
    return {
        # Page 1 (warrant face)
        'Dist.Info': court.get('district', ''),
        'Defendant1': name,
        'Defendant2': name,
        'Case number': form_data.get('case_number', ''),
        'Offense Description': (
            f"{off.get('code_section', '')}  {off.get('brief_description', '')}".strip()
        ),
        # Page 2 (sealed identifiers)
        'Defendant3': name,
        'Aliases': ', '.join(ident.get('aliases', [])),
        'Last Known residence': ident.get('last_known_residence', ''),
        'Prior addresses1': '; '.join(ident.get('prior_addresses', [])),
        'Last Known Employment': ident.get('last_known_employment', ''),
        'Last known telephone numbers': ', '.join(ident.get('phone_numbers', [])),
        'Place of birth': ident.get('place_of_birth', ''),
        'DOB': ident.get('date_of_birth', ''),
        'Social Security number': ident.get('ssn', ''),
        'Height': ident.get('height', ''),
        'Weight': ident.get('weight', ''),
        'Sex': ident.get('sex', ''),
        'Race': ident.get('race', ''),
        'Hair': ident.get('hair', ''),
        'Eyes': ident.get('eyes', ''),
        'Distinguishing marks1': ident.get('distinguishing_marks', ''),
        'History': ident.get('history_violence_weapons_drugs', ''),
        'Family1': associates,
        'FBI number': ident.get('fbi_number', ''),
        'Auto1': ident.get('vehicle_description', ''),
        'Agency address': ident.get('investigative_agency', ''),
    }


def fill_arrest_warrant(form_data, narrative, officer) -> bytes:
    text_map = _text_map(form_data)
    charge_state = CHARGING_ON_STATE.get(form_data.get('charging_document', ''))

    doc = fitz.open(AO442_PATH)
    for page in doc:
        for w in (page.widgets() or []):
            fn = w.field_name
            if fn in text_map and text_map[fn]:
                w.field_value = str(text_map[fn])
                w.update()
            elif fn == 'Document' and charge_state:
                ons = [s for s in w.button_states().get('normal', []) if s != 'Off']
                if ons and ons[0] == charge_state:
                    w.field_value = charge_state
                    w.update()

    # Append a supporting affidavit (extra pages) when a narrative is supplied.
    if narrative and narrative.strip():
        from .pdf import render_simple_pdf
        aff_bytes = render_simple_pdf('SUPPORTING AFFIDAVIT', narrative, officer)
        aff = fitz.open(stream=aff_bytes, filetype='pdf')
        doc.insert_pdf(aff)
        aff.close()

    out = io.BytesIO(doc.tobytes())
    doc.close()
    return out.getvalue()


def fill_search_warrant(form_data, narrative, officer) -> bytes:
    """
    Overlay the official (flat) AO 93 face form by anchor position, then append
    Attachment A / Attachment B / Affidavit pages.
    """
    court = form_data.get('court', {})
    district = court.get('district', '')
    prefix, _, state = district.partition(' District of ')  # "Central"/"California"
    execution = form_data.get('execution', {})

    doc = fitz.open(AO93_PATH)
    page = doc[0]

    def put(x, y, text, size=9):
        if text:
            page.insert_text((x, y), str(text), fontsize=size)

    # Caption: "for the ___ District of ___"
    put(232, 119, prefix)
    put(335, 119, state)
    # "located in the ___ District of ___"
    put(315, 284, prefix)
    put(415, 284, state)
    # Case number
    put(372, 172, form_data.get('case_number', ''))
    # Person/property to be searched (Attachment A reference)
    put(57, 312, 'See Attachment A.')
    # Items to be seized (below "such search will reveal")
    put(57, 410, 'See Attachment B.')
    # Execute on or before <date>
    put(350, 497, execution.get('execute_by_date', ''))
    # Daytime vs anytime checkbox
    if execution.get('time_window') == 'anytime':
        put(242, 512, 'X', 11)
    else:
        put(45, 512, 'X', 11)
    # Return to <magistrate judge>
    put(250, 593, court.get('judge_name', ''))

    # Append Attachment A / B / Affidavit pages.
    from .pdf import render_sw_attachments
    extra = render_sw_attachments(form_data, narrative, officer)
    ex = fitz.open(stream=extra, filetype='pdf')
    doc.insert_pdf(ex)
    ex.close()

    out = io.BytesIO(doc.tobytes())
    doc.close()
    return out.getvalue()

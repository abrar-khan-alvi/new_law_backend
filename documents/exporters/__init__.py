"""
Document exporters.

Public API:
    render_pdf(doc_type, form_data, narrative, officer)  -> bytes
    render_docx(doc_type, form_data, narrative, officer) -> BytesIO

Both dispatch on doc_type so each module (incident_report, search_warrant,
arrest_warrant) gets its own template — the export endpoint never assumes a
single layout.
"""
from .pdf import render_pdf
from .word import render_docx

__all__ = ['render_pdf', 'render_docx']

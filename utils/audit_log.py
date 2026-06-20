"""
Audit logging for sensitive actions (CJIS-oriented).

For now this writes structured lines to the 'audit' logger. It can be elevated
to a database-backed AuditLog model + CloudWatch handler in production without
changing call sites.
"""
import logging

audit = logging.getLogger('audit')


def _who(user):
    return getattr(user, 'email', 'anonymous')


def log_event(user, action: str, **details):
    detail_str = ' '.join(f'{k}={v}' for k, v in details.items())
    audit.info('user=%s action=%s %s', _who(user), action, detail_str)


def log_document_generation(user, doc_type, case_number=''):
    log_event(user, 'document.generate', doc_type=doc_type, case_number=case_number or '-')


def log_document_export(user, doc_id, export_format):
    log_event(user, 'document.export', doc_id=doc_id, format=export_format)


def log_document_access(user, doc_id):
    log_event(user, 'document.access', doc_id=doc_id)

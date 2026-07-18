"""
Audit logging for sensitive actions (CJIS-oriented).

Writes structured lines to the 'audit' logger AND persists a row to
admin_panel.models.AuditLog, which backs the admin Activity Monitor.
"""
import logging

audit = logging.getLogger('audit')


def _who(user):
    return getattr(user, 'email', None) or 'anonymous'


def log_event(user, action: str, severity: str = 'info', **details):
    detail_str = ' '.join(f'{k}={v}' for k, v in details.items())
    audit.info('user=%s action=%s severity=%s %s', _who(user), action, severity, detail_str)

    # Lazy import: this module is imported very early (views, signals) and
    # must not create a hard import-time dependency on the admin_panel app.
    from admin_panel.models import AuditLog
    try:
        AuditLog.objects.create(
            user=user if (user and getattr(user, 'is_authenticated', True)) else None,
            actor_label=_who(user),
            action=action,
            severity=severity,
            detail=detail_str[:500],
        )
    except Exception:
        # The audit trail is a secondary concern — never let a logging
        # failure (e.g. DB hiccup) break the primary request.
        audit.exception('Failed to persist AuditLog row for action=%s', action)


def log_document_generation(user, doc_type, case_number=''):
    log_event(user, 'document.generate', doc_type=doc_type, case_number=case_number or '-')


def log_document_export(user, doc_id, export_format):
    log_event(user, 'document.export', doc_id=doc_id, format=export_format)


def log_document_access(user, doc_id):
    log_event(user, 'document.access', doc_id=doc_id)

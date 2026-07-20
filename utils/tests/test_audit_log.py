"""
Regression test for audit log injection: a caller-supplied value containing
a newline must not be able to forge what looks like a separate audit log
entry (e.g. by embedding '\\n' plus a fake 'action=' token).
"""
from unittest.mock import patch

from django.test import TestCase

from utils.audit_log import log_event


class AuditLogInjectionTests(TestCase):
    @patch('utils.audit_log.audit')
    def test_newline_in_value_is_neutralized(self, mock_logger):
        malicious_case_number = 'LE-1\naction=document.delete severity=critical'
        log_event(None, 'document.generate', case_number=malicious_case_number)

        args = mock_logger.info.call_args[0]
        rendered = args[0] % args[1:]
        # The whole event must render as a single line — a real newline here
        # would let the forged "action=document.delete severity=critical"
        # text be mistaken for a second, separate audit log entry.
        self.assertEqual(rendered.count('\n'), 0)
        self.assertIn('\\n', rendered)

    @patch('utils.audit_log.audit')
    def test_persists_sanitized_detail_to_db(self, mock_logger):
        from admin_panel.models import AuditLog
        log_event(None, 'document.generate', case_number='LE-1\nforged=1')
        row = AuditLog.objects.latest('created_at')
        self.assertNotIn('\n', row.detail)

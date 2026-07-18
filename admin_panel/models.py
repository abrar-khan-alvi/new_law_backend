from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Append-only activity trail for the admin Activity Monitor. Written via
    utils.audit_log.log_event — never created directly from a view, so every
    call site funnels through the same severity/formatting rules.
    """

    class Severity(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='audit_logs',
    )
    # Snapshot of the actor's email at event time — keeps the trail readable
    # even after the user row is later deleted.
    actor_label = models.CharField(max_length=255, blank=True, default='anonymous')
    action = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    detail = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at} {self.action} ({self.actor_label})'

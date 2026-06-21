from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import GeneratedDocument


@shared_task
def cleanup_failed_documents(days: int = 30):
    """Delete failed document records older than `days`."""
    cutoff = timezone.now() - timedelta(days=days)
    qs = GeneratedDocument.objects.filter(status='failed', created_at__lt=cutoff)
    deleted, _ = qs.delete()
    return f'Deleted {deleted} failed documents older than {days} days.'

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .generation import run_generation
from .models import GeneratedDocument

logger = logging.getLogger(__name__)

# How long a document is allowed to sit in GENERATING before the periodic
# sweep below treats it as abandoned (e.g. the worker running its task was
# killed mid-generation) and reclaims it.
STUCK_GENERATING_MINUTES = 15


@shared_task
def cleanup_failed_documents(days: int = 30):
    """Delete failed document records older than `days`."""
    cutoff = timezone.now() - timedelta(days=days)
    qs = GeneratedDocument.objects.filter(status='failed', created_at__lt=cutoff)
    deleted, _ = qs.delete()
    return f'Deleted {deleted} failed documents older than {days} days.'


@shared_task(bind=True, max_retries=0)
def generate_document_task(self, doc_id, narrative_style, temperature=0.2,
                            sub_id=None, reserved_quota=False):
    """
    Runs generation for a document created (status=GENERATING) by the API
    view. Moving this off the request/gunicorn-worker thread and onto a
    Celery worker means a slow generation is bounded by CELERY_TASK_TIME_LIMIT
    instead of the much shorter gunicorn worker timeout — and if the Celery
    worker process itself dies mid-task, the document is left in GENERATING
    for reclaim_stuck_generating_documents() to find and close out below,
    rather than staying stuck forever with no cleanup path at all.
    """
    from subscriptions.models import Subscription, UsageLog

    try:
        doc = GeneratedDocument.objects.select_related('user').get(pk=doc_id)
    except GeneratedDocument.DoesNotExist:
        logger.error('generate_document_task: document %s no longer exists', doc_id)
        return

    try:
        run_generation(doc, narrative_style, temperature=temperature)
    except Exception as e:  # noqa: BLE001
        doc.status = GeneratedDocument.Status.FAILED
        doc.error_message = str(e)
        doc.save(update_fields=['status', 'error_message'])
        if reserved_quota and sub_id:
            sub = Subscription.objects.filter(pk=sub_id).first()
            if sub:
                sub.release_quota(doc.doc_type)
        return

    if sub_id:
        sub = Subscription.objects.filter(pk=sub_id).first()
        if sub:
            UsageLog.objects.create(
                user=doc.user, subscription=sub, doc_type=doc.doc_type,
                case_number=doc.case_number, tokens_used=doc.tokens_used,
            )


@shared_task
def reclaim_stuck_generating_documents(minutes: int = STUCK_GENERATING_MINUTES):
    """
    Closes the gap the worker-timeout finding called out: previously a
    document stuck mid-generation (worker SIGKILLed, Celery worker crashed,
    etc.) had no path back to a terminal state and no alert. Marks any
    document that's been sitting in GENERATING for longer than `minutes` as
    FAILED and releases its quota reservation, so the officer sees a clear
    failure (and can regenerate) instead of a document frozen forever.
    """
    cutoff = timezone.now() - timedelta(minutes=minutes)
    stuck = GeneratedDocument.objects.filter(
        status=GeneratedDocument.Status.GENERATING, updated_at__lt=cutoff,
    ).select_related('user__subscription')

    count = 0
    for doc in stuck:
        doc.status = GeneratedDocument.Status.FAILED
        doc.error_message = (
            'Generation did not complete in time and was automatically reclaimed. '
            'Please try again.'
        )
        doc.save(update_fields=['status', 'error_message'])

        # Admins bypass quota entirely (see GenerateDocumentView/
        # RegenerateDocumentView), so nothing was ever reserved for them —
        # only release for the non-admin path that actually reserved a slot.
        sub = getattr(doc.user, 'subscription', None)
        if doc.user.role != 'admin' and sub:
            sub.release_quota(doc.doc_type)
        count += 1

    if count:
        logger.warning('Reclaimed %d document(s) stuck in GENERATING past %d minutes.', count, minutes)
    return f'Reclaimed {count} stuck document(s).'

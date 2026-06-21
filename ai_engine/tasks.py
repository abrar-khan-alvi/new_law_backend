import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def index_training_document(self, training_doc_id: int):
    """Async: chunk + embed a training document after upload."""
    from .models import TrainingDocument
    from .rag_pipeline import index_document

    try:
        doc = TrainingDocument.objects.get(pk=training_doc_id)
        count = index_document(doc)
        return f'Indexed {count} chunks for training doc {training_doc_id}.'
    except Exception as exc:  # noqa: BLE001
        logger.exception('Indexing failed for %s', training_doc_id)
        raise self.retry(exc=exc, countdown=60)

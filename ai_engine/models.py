from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField


class TrainingDocument(models.Model):
    """An admin-uploaded sample document used to teach the AI house style."""

    class DocType(models.TextChoices):
        INCIDENT_REPORT = 'incident_report', 'Incident Report'
        SEARCH_WARRANT = 'search_warrant', 'Search Warrant'
        ARREST_WARRANT = 'arrest_warrant', 'Arrest Warrant'

    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    title = models.CharField(max_length=300, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    s3_key = models.CharField(max_length=500, blank=True)   # stored original file
    raw_text = models.TextField(blank=True)                 # extracted text (re-indexable)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='training_documents',
    )
    is_indexed = models.BooleanField(default=False)
    chunk_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'training_documents'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['doc_type', 'is_indexed'])]

    def __str__(self):
        return f'{self.title or self.original_filename} ({self.doc_type})'


class DocumentChunk(models.Model):
    """A text chunk of a training document + its embedding (pgvector)."""

    training_doc = models.ForeignKey(
        TrainingDocument, on_delete=models.CASCADE, related_name='chunks',
    )
    doc_type = models.CharField(max_length=30, db_index=True)
    chunk_index = models.PositiveIntegerField(default=0)
    text = models.TextField()
    embedding = VectorField(dimensions=384)  # all-MiniLM-L6-v2 → 384 dims
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_chunks'
        ordering = ['training_doc_id', 'chunk_index']
        indexes = [
            HnswIndex(
                name='chunk_embedding_hnsw',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]

    def __str__(self):
        return f'chunk {self.chunk_index} of doc {self.training_doc_id}'

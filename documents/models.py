import uuid

from django.conf import settings
from django.db import models


class GeneratedDocument(models.Model):

    class DocType(models.TextChoices):
        INCIDENT_REPORT = 'incident_report', 'Incident Report'
        SEARCH_WARRANT = 'search_warrant', 'Search Warrant'
        ARREST_WARRANT = 'arrest_warrant', 'Arrest Warrant'

    class NarrativeStyle(models.TextChoices):
        FIRST_PERSON = 'first_person', 'First Person (I, my)'
        THIRD_PERSON = 'third_person', 'Third Person (Officer name)'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        GENERATING = 'generating', 'Generating'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents',
    )
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    case_number = models.CharField(max_length=50, blank=True, db_index=True)
    form_data = models.JSONField()
    ai_narrative = models.TextField(blank=True)
    narrative_style = models.CharField(
        max_length=20, choices=NarrativeStyle.choices,
        default=NarrativeStyle.FIRST_PERSON,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    error_message = models.TextField(blank=True)

    # S3 export keys (populated in Step 9 when AWS is configured)
    s3_pdf_key = models.CharField(max_length=500, blank=True)
    s3_docx_key = models.CharField(max_length=500, blank=True)

    # AI metadata
    model_used = models.CharField(max_length=100, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    generation_time_ms = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'generated_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'doc_type']),
            models.Index(fields=['case_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.doc_type} — {self.case_number or self.id} ({self.user.email})"

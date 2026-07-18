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
    # For search/arrest warrants: just the AI-authored factual narrative, i.e.
    # ai_narrative minus the fixed, pre-approved template intro/closing sections
    # (requirement: AI organizes facts into predefined sections, doesn't author
    # the legal language itself). Equals ai_narrative for incident reports.
    narrative_body = models.TextField(blank=True)
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

    # Post-generation leak/hallucination check: ungrounded details for officer
    # review, e.g. [{"type": "proper_noun", "value": "DoorDash"}]. Empty = clean.
    leak_flags = models.JSONField(default=list, blank=True)

    # Constitutional Quality Review flags (e.g. missing citations, missing nexus)
    quality_flags = models.JSONField(default=list, blank=True)

    # ── Supervisor / prosecutor review workflow (Agency Configuration Wizard) ─
    class ReviewStatus(models.TextChoices):
        NOT_REQUIRED = 'not_required', 'Not Required'
        PENDING_SUPERVISOR = 'pending_supervisor', 'Pending Supervisor Review'
        PENDING_PROSECUTOR = 'pending_prosecutor', 'Pending Prosecutor Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    review_status = models.CharField(
        max_length=30, choices=ReviewStatus.choices, default=ReviewStatus.NOT_REQUIRED,
    )
    supervisor_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='supervisor_reviewed_documents',
    )
    supervisor_reviewed_at = models.DateTimeField(null=True, blank=True)
    supervisor_notes = models.TextField(blank=True)

    # Prosecutor review is tracked as external metadata — prosecutors don't log in.
    prosecutor_reviewed_name = models.CharField(max_length=200, blank=True)
    prosecutor_reviewed_at = models.DateTimeField(null=True, blank=True)
    prosecutor_approved = models.BooleanField(null=True, blank=True)
    prosecutor_notes = models.TextField(blank=True)

    # ── Built-in electronic signature (typed name + timestamp + IP) ──────────
    signature_name = models.CharField(max_length=200, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_ip = models.GenericIPAddressField(null=True, blank=True)

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


class WarrantTemplate(models.Model):
    """
    Pre-approved legal-language sections for search/arrest warrants (requirement:
    "rules-based, pre-approved legal templates populated by AI... AI organizes
    officer-provided facts into predefined legal sections, not invent legal
    language"). `template_text` holds fixed, admin-editable legal phrasing with
    named {placeholder} tokens filled directly from officer-provided facts — the
    AI never authors this text (see ai_engine/prompt_builder.py + documents.
    templates_engine, which only draft/assemble the factual narrative in between).

    Exactly one of `agency` / `jurisdiction_profile` should be set: an agency-level
    row overrides its jurisdiction profile's row, which overrides the built-in
    global default in documents.templates_engine.DEFAULT_TEMPLATES.
    """
    class DocType(models.TextChoices):
        SEARCH_WARRANT = 'search_warrant', 'Search Warrant'
        ARREST_WARRANT = 'arrest_warrant', 'Arrest Warrant'

    class Section(models.TextChoices):
        AFFIDAVIT_INTRO = 'affidavit_intro', 'Affidavit Introduction'
        NEXUS_CLOSING = 'nexus_closing', 'Nexus / Probable Cause Closing (search warrants)'
        ELEMENTS_CLOSING = 'elements_closing', 'Elements / Probable Cause Closing (arrest warrants)'

    agency = models.ForeignKey(
        'accounts.Agency', on_delete=models.CASCADE, null=True, blank=True,
        related_name='warrant_templates',
    )
    jurisdiction_profile = models.ForeignKey(
        'accounts.JurisdictionProfile', on_delete=models.CASCADE, null=True, blank=True,
        related_name='warrant_templates',
    )
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    section_key = models.CharField(max_length=30, choices=Section.choices)
    # Only meaningful for global rows (agency and jurisdiction_profile both
    # null) — lets the seeded global defaults still vary by jurisdiction level
    # (requirement #3) even with no agency/profile configured yet. Ignored for
    # agency- or profile-scoped rows, since those already imply one jurisdiction.
    jurisdiction_type = models.CharField(
        max_length=50, choices=[
            ('federal', 'Federal'), ('state', 'State'), ('municipal', 'Municipal/County'),
        ], blank=True,
    )
    template_text = models.TextField(
        help_text='Pre-approved legal language with {placeholder} tokens. '
                   'Have counsel review before use on a real filing.'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'warrant_templates'
        indexes = [models.Index(fields=['doc_type', 'section_key'])]

    def __str__(self):
        scope = self.agency or self.jurisdiction_profile or f'global/{self.jurisdiction_type or "state"}'
        return f"{self.doc_type}/{self.section_key} — {scope}"

import time

import shortuuid
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOfficer, IsOwnerOrAdmin, IsSupervisorOfAgency
from ai_engine.leak_check import check_narrative
from ai_engine.model_client import ModelClient
from ai_engine.postprocess import clean_narrative
from ai_engine.prompt_builder import PROMPT_BUILDERS
from ai_engine.quality_review import (
    check_constitutional_quality,
    consistency_review,
    structural_review,
)
from subscriptions.models import UsageLog
from utils.audit_log import (
    log_document_access,
    log_document_export,
    log_document_generation,
)
from utils.exceptions import QuotaExceeded
from utils.pagination import StandardPagination

from .exporters import render_docx, render_pdf
from .models import GeneratedDocument
from .serializers import (
    GeneratedDocumentListSerializer,
    GeneratedDocumentSerializer,
    GenerateRequestSerializer,
)
from .templates_engine import get_template_text, render_template

# Doc types that use the rules-based legal template (requirement #2) instead of
# a freely-drafted narrative — the AI only writes the connecting factual body.
WARRANT_SECTIONS = {
    'search_warrant': ('affidavit_intro', 'nexus_closing'),
    'arrest_warrant': ('affidavit_intro', 'elements_closing'),
}

_DOCX_CONTENT_TYPE = (
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
)

# Required before an incident report can be exported — previously, a blank
# department_name/ori/badge_number here silently rendered a real (but wrong)
# department's identity onto the document instead of blocking export.
INCIDENT_REPORT_REQUIRED_OFFICER_FIELDS = [
    ('department_name', 'department name'),
    ('ori', 'ORI'),
    ('badge_number', 'badge number'),
]


def _officer_profile(user) -> dict:
    """Profile fields auto-injected into every document (not in form_data)."""
    profile = {
        'full_name': user.full_name,
        'rank': user.rank,
        'badge_number': user.badge_number,
        'department_name': user.department_name,
        'department_address': user.department_address,
        'department_state': user.department_state,
        'ori': user.ori,
        'phone': user.phone_number,
        'email': user.email,
    }

    agency = user.agency
    if agency:
        from utils.storage import media_url

        profile.update({
            'agency_id': agency.id,
            'agency_name': agency.name,
            'agency_jurisdiction_type': agency.jurisdiction_type,
            'agency_state': agency.state,
            'agency_county': agency.county,
            'agency_city': agency.city,
            'agency_court_name': agency.court_name,
            'agency_judicial_district': agency.judicial_district,
            'agency_division': agency.division,
            'agency_court_caption': agency.court_caption,
            'agency_judge_title': agency.judge_title,
            'agency_prosecuting_authority': agency.prosecuting_authority,
            'agency_case_number_format': agency.case_number_format,
            'agency_default_legal_citations': agency.effective_legal_citations(),
            'agency_seal_key': agency.seal_image_key or None,
            'agency_seal_url': media_url(agency.seal_image_key) if agency.seal_image_key else None,
            'agency_requires_supervisor_review': agency.requires_supervisor_review,
            'agency_requires_prosecutor_review': agency.requires_prosecutor_review,
        })
        # Override legacy fields if agency is set
        profile['department_name'] = agency.name
        profile['department_state'] = agency.state
        profile['ori'] = agency.ori

    return profile


def _warrant_template_values(doc_type, form_data, officer):
    """Placeholder values for the fixed legal-template sections — all sourced
    directly from officer-provided facts, never from the AI."""
    values = {
        'affiant_name': officer.get('full_name', ''),
        'rank': officer.get('rank', ''),
        'agency_name': officer.get('agency_name') or officer.get('department_name', ''),
    }
    if doc_type == 'search_warrant':
        pc = form_data.get('probable_cause', {})
        place = form_data.get('place_to_search', {})
        offenses = ', '.join(
            f"{o.get('code_section', '')} ({o.get('description', '')})"
            for o in form_data.get('offenses', [])
        )
        values.update({
            'offenses': offenses,
            'place_description': place.get('description', ''),
            'nexus_to_place': pc.get('nexus_to_place', ''),
        })
    elif doc_type == 'arrest_warrant':
        offense = form_data.get('offense', {})
        values.update({
            'defendant_name': form_data.get('defendant', {}).get('full_name', ''),
            'offense_description': offense.get('brief_description', ''),
            'code_section': offense.get('code_section', ''),
        })
    return values


def _default_review_status(doc_type, agency):
    if doc_type not in WARRANT_SECTIONS or not agency:
        return GeneratedDocument.ReviewStatus.NOT_REQUIRED
    if agency.requires_supervisor_review:
        return GeneratedDocument.ReviewStatus.PENDING_SUPERVISOR
    if agency.requires_prosecutor_review:
        return GeneratedDocument.ReviewStatus.PENDING_PROSECUTOR
    return GeneratedDocument.ReviewStatus.NOT_REQUIRED


def _run_generation(doc, narrative_style, temperature=0.2):
    """Build the prompt, call the model, assemble + persist the narrative. Raises on failure."""
    officer = _officer_profile(doc.user)
    builder = PROMPT_BUILDERS[doc.doc_type]
    prompt = builder(doc.form_data, officer, narrative_style)

    start = time.time()
    client = ModelClient()
    if prompt:
        ai_text = client.generate(prompt, max_tokens=3000, temperature=temperature)
        # Strip Markdown / echoed signature blocks the model may add (model-independent).
        ai_text = clean_narrative(ai_text, officer)
    else:
        # No facts supplied for the AI to organize (e.g. an arrest warrant with
        # no probable-cause narrative) — the fixed template sections still stand.
        ai_text = ''
    elapsed = int((time.time() - start) * 1000)

    if doc.doc_type in WARRANT_SECTIONS:
        # Rules-based template: fixed, pre-approved legal sections (requirement
        # #2) with jurisdiction-specific phrasing (requirement #3) wrap the
        # AI-authored factual narrative. The AI never writes the legal-
        # conclusion sentences — see ai_engine/prompt_builder.py.
        intro_key, closing_key = WARRANT_SECTIONS[doc.doc_type]
        agency = doc.user.agency
        jurisdiction_override = doc.form_data.get('court', {}).get('jurisdiction_type_override')
        values = _warrant_template_values(doc.doc_type, doc.form_data, officer)

        intro = render_template(
            get_template_text(agency, doc.doc_type, intro_key, jurisdiction_override), values)
        closing = render_template(
            get_template_text(agency, doc.doc_type, closing_key, jurisdiction_override), values)

        doc.narrative_body = ai_text
        assembled = '\n\n'.join(part.strip() for part in [intro, ai_text, closing] if part and part.strip())
        doc.review_status = _default_review_status(doc.doc_type, agency)
    else:
        doc.narrative_body = ai_text
        assembled = ai_text

    # Deterministic post-generation leak/hallucination check — run against the
    # AI-authored portion only; the templated intro/closing can't hallucinate.
    doc.leak_flags = check_narrative(doc.narrative_body, doc.form_data, officer)

    # Constitutional Quality Review: deterministic structural/consistency checks
    # (never depend on the LLM, so they can't silently fail open) run against
    # form_data/the assembled text, plus the LLM-based review — merged into one
    # flag list.
    doc.quality_flags = (
        structural_review(doc.doc_type, doc.form_data)
        + consistency_review(doc.doc_type, assembled, doc.form_data)
        + check_constitutional_quality(doc.doc_type, assembled)
    )

    doc.ai_narrative = assembled
    doc.status = GeneratedDocument.Status.COMPLETED
    doc.generation_time_ms = elapsed
    doc.model_used = client.model_name
    doc.save()
    return assembled


class GenerateDocumentView(APIView):
    """POST /api/documents/generate/ — create + generate a document."""
    permission_classes = [IsOfficer]

    def post(self, request):
        serializer = GenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_type = serializer.validated_data['doc_type']
        narrative_style = serializer.validated_data['narrative_style']
        form_data = serializer.validated_data['form_data']

        user = request.user
        is_admin = user.role == 'admin'
        sub = getattr(user, 'subscription', None)

        # ── Plan & quota gating (admins bypass) ──────────────────────
        reserved_quota = False
        if not is_admin:
            if not sub or sub.status not in ('active', 'trialing'):
                return Response(
                    {'error': {'detail': 'No active subscription.', 'code': 'no_subscription'}},
                    status=403,
                )
            if not sub.plan.allows_doc_type(doc_type):
                return Response(
                    {'error': {'detail': f'Your plan does not include {doc_type}.',
                               'code': 'module_not_in_plan'}},
                    status=403,
                )
            # Atomic reserve — closes the check-then-increment race that let
            # concurrent requests both slip through a plain read-then-write
            # check. Incident reports and warrants draw from separate quota
            # buckets (Plan.document_limit vs Plan.warrant_document_limit).
            if not sub.try_reserve_quota(doc_type):
                raise QuotaExceeded()
            reserved_quota = True

        case_number = form_data.get('case_number') or f"LE-{shortuuid.uuid()[:10].upper()}"
        # Persist the resolved case number into form_data so exporters render it.
        form_data['case_number'] = case_number

        doc = GeneratedDocument.objects.create(
            user=user,
            doc_type=doc_type,
            case_number=case_number,
            form_data=form_data,
            narrative_style=narrative_style,
            status=GeneratedDocument.Status.GENERATING,
        )

        try:
            _run_generation(doc, narrative_style)
        except Exception as e:  # noqa: BLE001
            doc.status = GeneratedDocument.Status.FAILED
            doc.error_message = str(e)
            doc.save(update_fields=['status', 'error_message'])
            if reserved_quota:
                # A failed generation shouldn't cost the user their quota.
                sub.release_quota(doc_type)
            return Response(
                {'error': {'detail': f'AI generation failed: {e}', 'code': 'generation_failed'}},
                status=503,
            )

        # ── Usage accounting ─────────────────────────────────────────
        # (the increment itself already happened atomically in try_reserve_quota)
        if sub:
            UsageLog.objects.create(
                user=user, subscription=sub, doc_type=doc_type,
                case_number=case_number, tokens_used=doc.tokens_used,
            )
        log_document_generation(user, doc_type, case_number)

        return Response(GeneratedDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


class RegenerateDocumentView(APIView):
    """
    POST /api/documents/<pk>/regenerate/ — re-run generation for a document.
    Regeneration is available on every plan (it's a correctness feature, not a
    premium perk — a flagged narrative shouldn't be a dead end just because a
    user is on Free) but it draws from the same quota bucket generating that
    doc type would: free on a plan where that bucket is unlimited, metered
    otherwise.
    """
    permission_classes = [IsOfficer]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.get(pk=pk, user=request.user)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)

        user = request.user
        is_admin = user.role == 'admin'
        sub = getattr(user, 'subscription', None)

        reserved_quota = False
        if not is_admin:
            if not sub or sub.status not in ('active', 'trialing'):
                return Response(
                    {'error': {'detail': 'No active subscription.', 'code': 'no_subscription'}},
                    status=403,
                )
            if not sub.try_reserve_quota(doc.doc_type):
                raise QuotaExceeded()
            reserved_quota = True

        doc.status = GeneratedDocument.Status.GENERATING
        doc.save(update_fields=['status'])
        try:
            # Slightly higher temperature for variation on regenerate.
            _run_generation(doc, doc.narrative_style, temperature=0.3)
        except Exception as e:  # noqa: BLE001
            doc.status = GeneratedDocument.Status.FAILED
            doc.error_message = str(e)
            doc.save(update_fields=['status', 'error_message'])
            if reserved_quota:
                sub.release_quota(doc.doc_type)
            return Response(
                {'error': {'detail': f'AI generation failed: {e}', 'code': 'generation_failed'}},
                status=503,
            )

        if sub:
            UsageLog.objects.create(
                user=user, subscription=sub, doc_type=doc.doc_type,
                case_number=doc.case_number, tokens_used=doc.tokens_used,
            )
        return Response(GeneratedDocumentSerializer(doc).data)


class DocumentListView(APIView):
    """GET /api/documents/ — current officer's document history (paginated)."""
    permission_classes = [IsOfficer]

    def get(self, request):
        qs = GeneratedDocument.objects.filter(user=request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        data = GeneratedDocumentListSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


class DocumentDetailView(APIView):
    """GET /api/documents/<pk>/ — full document (owner or admin)."""
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, pk):
        try:
            doc = GeneratedDocument.objects.get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Not found.'}}, status=404)
        self.check_object_permissions(request, doc)
        log_document_access(request.user, str(doc.id))
        return Response(GeneratedDocumentSerializer(doc).data)


class ExportDocumentView(APIView):
    """
    POST /api/documents/<pk>/export/
    Body: {"format": "pdf"|"docx", "edited_text": "<optional officer-edited narrative>"}
    """
    permission_classes = [IsOfficer]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.get(pk=pk, user=request.user)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)

        export_format = (request.data.get('format') or 'pdf').lower()
        if export_format not in ('pdf', 'docx'):
            return Response(
                {'error': {'detail': 'Invalid format. Use pdf or docx.'}}, status=400)

        # Plan-based export gating (admins bypass). Bypass entirely in development (DEBUG).
        user = request.user
        if user.role != 'admin' and not getattr(settings, 'DEBUG', False):
            plan = getattr(getattr(user, 'subscription', None), 'plan', None)
            allowed = plan and (
                plan.can_export_pdf if export_format == 'pdf' else plan.can_export_docx
            )
            if not allowed:
                return Response(
                    {'error': {'detail': f'Your plan does not allow {export_format} export.',
                               'code': 'export_not_in_plan'}},
                    status=403,
                )

        narrative = request.data.get('edited_text') or doc.ai_narrative
        officer = _officer_profile(user)

        # Never silently substitute another department's identity onto a real
        # filing — require the officer's own profile to be complete instead.
        missing = [
            label for field, label in INCIDENT_REPORT_REQUIRED_OFFICER_FIELDS
            if doc.doc_type == 'incident_report' and not officer.get(field)
        ]
        if missing:
            return Response(
                {'error': {
                    'detail': f"Your officer profile is missing required information ({', '.join(missing)}) "
                              "needed to export an incident report. Update your profile before exporting.",
                    'code': 'incomplete_officer_profile',
                }},
                status=400,
            )

        filename = f"{doc.doc_type}_{doc.case_number or doc.id}".replace(' ', '_')
        doc_meta = {
            'review_status': doc.review_status,
            'signature_name': doc.signature_name or None,
            'signed_at': doc.signed_at.strftime('%Y-%m-%d %H:%M %Z') if doc.signed_at else None,
        }

        log_document_export(user, str(doc.id), export_format)

        if export_format == 'pdf':
            content = render_pdf(doc.doc_type, doc.form_data, narrative, officer, doc_meta)
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

        buf = render_docx(doc.doc_type, doc.form_data, narrative, officer, doc_meta)
        response = HttpResponse(buf.getvalue(), content_type=_DOCX_CONTENT_TYPE)
        response['Content-Disposition'] = f'attachment; filename="{filename}.docx"'
        return response


class SupervisorReviewView(APIView):
    """
    POST /api/documents/<pk>/supervisor-review/
    Body: {"approved": bool, "notes": "..."}
    Supervisor (same agency) or admin only.
    """
    permission_classes = [IsSupervisorOfAgency]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.select_related('user').get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)
        self.check_object_permissions(request, doc)

        approved = bool(request.data.get('approved'))
        doc.supervisor_reviewed_by = request.user
        doc.supervisor_reviewed_at = timezone.now()
        doc.supervisor_notes = request.data.get('notes', '') or ''
        if not approved:
            doc.review_status = GeneratedDocument.ReviewStatus.REJECTED
        elif doc.user.agency and doc.user.agency.requires_prosecutor_review:
            doc.review_status = GeneratedDocument.ReviewStatus.PENDING_PROSECUTOR
        else:
            doc.review_status = GeneratedDocument.ReviewStatus.APPROVED
        doc.save(update_fields=[
            'supervisor_reviewed_by', 'supervisor_reviewed_at', 'supervisor_notes', 'review_status',
        ])
        return Response(GeneratedDocumentSerializer(doc).data)


class ProsecutorReviewView(APIView):
    """
    POST /api/documents/<pk>/prosecutor-review/
    Body: {"reviewer_name": "...", "approved": bool, "notes": "..."}
    Recorded by a supervisor or admin on the prosecutor's behalf — prosecutors
    are external to the department and don't get logins to this system.
    """
    permission_classes = [IsSupervisorOfAgency]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.select_related('user').get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)
        self.check_object_permissions(request, doc)

        reviewer_name = (request.data.get('reviewer_name') or '').strip()
        if not reviewer_name:
            return Response({'error': {'detail': 'reviewer_name is required.'}}, status=400)

        approved = bool(request.data.get('approved'))
        doc.prosecutor_reviewed_name = reviewer_name
        doc.prosecutor_reviewed_at = timezone.now()
        doc.prosecutor_approved = approved
        doc.prosecutor_notes = request.data.get('notes', '') or ''
        doc.review_status = (
            GeneratedDocument.ReviewStatus.APPROVED if approved
            else GeneratedDocument.ReviewStatus.REJECTED
        )
        doc.save(update_fields=[
            'prosecutor_reviewed_name', 'prosecutor_reviewed_at', 'prosecutor_approved',
            'prosecutor_notes', 'review_status',
        ])
        return Response(GeneratedDocumentSerializer(doc).data)


class SignDocumentView(APIView):
    """
    POST /api/documents/<pk>/sign/
    Body: {"full_name": "..."}
    Built-in electronic signature: typed name + timestamp + IP (owner or a
    supervisor at the same agency).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.select_related('user').get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)

        user = request.user
        is_owner = doc.user_id == user.id
        is_supervisor_same_agency = (
            user.is_supervisor and doc.user.agency_id and user.agency_id == doc.user.agency_id
        )
        if not (is_owner or is_supervisor_same_agency or user.role == 'admin'):
            return Response({'error': {'detail': 'Not permitted to sign this document.'}}, status=403)

        full_name = (request.data.get('full_name') or '').strip()
        if not full_name:
            return Response({'error': {'detail': 'full_name is required.'}}, status=400)

        doc.signature_name = full_name
        doc.signed_at = timezone.now()
        doc.signed_ip = request.META.get('REMOTE_ADDR')
        doc.save(update_fields=['signature_name', 'signed_at', 'signed_ip'])
        return Response(GeneratedDocumentSerializer(doc).data)

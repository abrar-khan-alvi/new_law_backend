import time

import shortuuid
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsVerifiedOfficer, IsOwnerOrAdmin
from ai_engine.leak_check import check_narrative
from ai_engine.model_client import ModelClient
from ai_engine.postprocess import clean_narrative
from ai_engine.prompt_builder import PROMPT_BUILDERS
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

_DOCX_CONTENT_TYPE = (
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
)


def _officer_profile(user) -> dict:
    """Profile fields auto-injected into every document (not in form_data)."""
    return {
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


def _run_generation(doc, narrative_style, temperature=0.2):
    """Build the prompt, call the model, persist the narrative. Raises on failure."""
    officer = _officer_profile(doc.user)
    builder = PROMPT_BUILDERS[doc.doc_type]
    prompt = builder(doc.form_data, officer, narrative_style)

    start = time.time()
    client = ModelClient()
    ai_text = client.generate(prompt, max_tokens=3000, temperature=temperature)
    elapsed = int((time.time() - start) * 1000)

    # Strip Markdown / echoed signature blocks the model may add (model-independent).
    ai_text = clean_narrative(ai_text, officer)

    # Deterministic post-generation leak/hallucination check (flags, never edits).
    doc.leak_flags = check_narrative(ai_text, doc.form_data, officer)

    doc.ai_narrative = ai_text
    doc.status = GeneratedDocument.Status.COMPLETED
    doc.generation_time_ms = elapsed
    doc.model_used = client.model_name
    doc.save()
    return ai_text


class GenerateDocumentView(APIView):
    """POST /api/documents/generate/ — create + generate a document."""
    permission_classes = [IsVerifiedOfficer]

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
        if not is_admin:
            if not sub or sub.status != 'active':
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
            if not user.can_generate_document:
                raise QuotaExceeded()

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
            return Response(
                {'error': {'detail': f'AI generation failed: {e}', 'code': 'generation_failed'}},
                status=503,
            )

        # ── Usage accounting ─────────────────────────────────────────
        if sub:
            sub.documents_generated_this_month += 1
            sub.save(update_fields=['documents_generated_this_month'])
            UsageLog.objects.create(
                user=user, subscription=sub, doc_type=doc_type,
                case_number=case_number, tokens_used=doc.tokens_used,
            )
        log_document_generation(user, doc_type, case_number)

        return Response(GeneratedDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


class RegenerateDocumentView(APIView):
    """POST /api/documents/<pk>/regenerate/ — re-run generation for a document."""
    permission_classes = [IsVerifiedOfficer]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.get(pk=pk, user=request.user)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)

        user = request.user
        if user.role != 'admin':
            sub = getattr(user, 'subscription', None)
            if not sub or not sub.plan.can_regenerate:
                return Response(
                    {'error': {'detail': 'Your plan does not allow regeneration.',
                               'code': 'regenerate_not_in_plan'}},
                    status=403,
                )

        doc.status = GeneratedDocument.Status.GENERATING
        doc.save(update_fields=['status'])
        try:
            # Slightly higher temperature for variation on regenerate.
            _run_generation(doc, doc.narrative_style, temperature=0.3)
        except Exception as e:  # noqa: BLE001
            doc.status = GeneratedDocument.Status.FAILED
            doc.error_message = str(e)
            doc.save(update_fields=['status', 'error_message'])
            return Response(
                {'error': {'detail': f'AI generation failed: {e}', 'code': 'generation_failed'}},
                status=503,
            )
        return Response(GeneratedDocumentSerializer(doc).data)


class DocumentListView(APIView):
    """GET /api/documents/ — current officer's document history (paginated)."""
    permission_classes = [IsVerifiedOfficer]

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
    permission_classes = [IsVerifiedOfficer]

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
        filename = f"{doc.doc_type}_{doc.case_number or doc.id}".replace(' ', '_')

        log_document_export(user, str(doc.id), export_format)

        if export_format == 'pdf':
            content = render_pdf(doc.doc_type, doc.form_data, narrative, officer)
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

        buf = render_docx(doc.doc_type, doc.form_data, narrative, officer)
        response = HttpResponse(buf.getvalue(), content_type=_DOCX_CONTENT_TYPE)
        response['Content-Disposition'] = f'attachment; filename="{filename}.docx"'
        return response

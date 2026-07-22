import shortuuid
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOfficer, IsOwnerOrAdmin, IsSupervisorOfAgency
from utils.audit_log import (
    log_document_access,
    log_document_export,
    log_document_generation,
)
from utils.exceptions import QuotaExceeded
from utils.pagination import StandardPagination

from .exporters import render_docx, render_pdf
from .generation import WARRANT_SECTIONS, _officer_profile
from .models import GeneratedDocument
from .serializers import (
    GeneratedDocumentListSerializer,
    GeneratedDocumentSerializer,
    GenerateRequestSerializer,
)
from .tasks import generate_document_task

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


def _auto_case_number(user):
    """
    Auto-generated case number honoring the agency's admin-configured
    case_number_format (Agency Configuration Wizard). Supported tokens:
    YYYY / YY / MM / DD (today's date) and runs of '#' (random digits),
    e.g. "SW-YYYY-#####" -> "SW-2026-40173". Falls back to LE-<uuid>.
    """
    import re
    import secrets

    fmt = getattr(getattr(user, 'agency', None), 'case_number_format', '') or ''
    if not fmt:
        return f"LE-{shortuuid.uuid()[:10].upper()}"
    now = timezone.now()
    number = (fmt.replace('YYYY', now.strftime('%Y')).replace('YY', now.strftime('%y'))
              .replace('MM', now.strftime('%m')).replace('DD', now.strftime('%d')))
    number = re.sub(
        r'#+', lambda m: ''.join(secrets.choice('0123456789') for _ in m.group()), number)
    if '#' not in fmt:
        # No random component in the format — append one so numbers stay unique.
        number = f"{number}{shortuuid.uuid()[:6].upper()}"
    return number


class GenerateDocumentView(APIView):
    """
    POST /api/documents/generate/ — create a document and hand generation off
    to a Celery worker. Returns immediately with status=GENERATING; poll
    GET /api/documents/<pk>/ for completion. Generation used to run inline on
    the request/gunicorn-worker thread, where a worker timeout would SIGKILL
    the process mid-generation and leave the document stuck in GENERATING
    forever with no cleanup path — moving it onto a Celery task (bounded by
    CELERY_TASK_TIME_LIMIT, plus documents.tasks.reclaim_stuck_generating_documents
    as a backstop) closes that gap.
    """
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

        case_number = form_data.get('case_number') or _auto_case_number(user)
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

        generate_document_task.delay(
            str(doc.id), narrative_style,
            sub_id=sub.id if sub else None, reserved_quota=reserved_quota,
        )
        log_document_generation(user, doc_type, case_number)

        return Response(GeneratedDocumentSerializer(doc).data, status=status.HTTP_202_ACCEPTED)


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

        # Regenerated content invalidates any prior approval/signature — an
        # export taken between regenerate and the next review must not show a
        # signature that never actually attested to the new content.
        doc.status = GeneratedDocument.Status.GENERATING
        doc.supervisor_reviewed_by = None
        doc.supervisor_reviewed_at = None
        doc.supervisor_notes = ''
        doc.prosecutor_reviewed_name = ''
        doc.prosecutor_reviewed_at = None
        doc.prosecutor_approved = None
        doc.prosecutor_notes = ''
        doc.signature_name = ''
        doc.signed_at = None
        doc.signed_ip = None
        doc.save(update_fields=[
            'status', 'supervisor_reviewed_by', 'supervisor_reviewed_at', 'supervisor_notes',
            'prosecutor_reviewed_name', 'prosecutor_reviewed_at', 'prosecutor_approved', 'prosecutor_notes',
            'signature_name', 'signed_at', 'signed_ip',
        ])
        # Slightly higher temperature for variation on regenerate.
        generate_document_task.delay(
            str(doc.id), doc.narrative_style, temperature=0.3,
            sub_id=sub.id if sub else None, reserved_quota=reserved_quota,
        )
        return Response(GeneratedDocumentSerializer(doc).data, status=status.HTTP_202_ACCEPTED)


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
            doc = GeneratedDocument.objects.select_related('user').get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)

        user = request.user
        # Owner or admin — an admin needs to be able to export/file a document
        # they just approved, not just review and sign it.
        if doc.user_id != user.id and user.role != 'admin':
            return Response({'error': {'detail': 'Not permitted to export this document.'}}, status=403)

        export_format = (request.data.get('format') or 'pdf').lower()
        if export_format not in ('pdf', 'docx'):
            return Response(
                {'error': {'detail': 'Invalid format. Use pdf or docx.'}}, status=400)

        # Plan-based export gating is based on the REQUESTER's plan (it's
        # their action being metered), not the document owner's.
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
        # Always the document OWNER's identity — an admin exporting on an
        # officer's behalf must not stamp the admin's own badge/ORI onto it.
        officer = _officer_profile(doc.user)

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

        # Warrants render a jurisdiction-specific legal header/caption from the
        # officer's Agency (state, court, judicial district, etc. — see
        # requirement #1 in the Requirements docx). With no agency assigned,
        # that header would silently export blank instead of blocking on it —
        # an admin must assign the officer to an agency first.
        if doc.doc_type in WARRANT_SECTIONS and not doc.user.agency:
            return Response(
                {'error': {
                    'detail': 'This officer is not assigned to an agency, so the jurisdiction '
                              'header (state, court, judicial district, etc.) cannot be generated. '
                              'An admin must assign an agency before this document can be exported.',
                    'code': 'missing_agency',
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
        if doc.status != GeneratedDocument.Status.COMPLETED:
            return Response(
                {'error': {'detail': 'Only a completed document can be reviewed.',
                           'code': 'document_not_completed'}},
                status=400,
            )

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
        if doc.status != GeneratedDocument.Status.COMPLETED:
            return Response(
                {'error': {'detail': 'Only a completed document can be reviewed.',
                           'code': 'document_not_completed'}},
                status=400,
            )

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
        if doc.status != GeneratedDocument.Status.COMPLETED:
            return Response(
                {'error': {'detail': 'Only a completed document can be signed.',
                           'code': 'document_not_completed'}},
                status=400,
            )

        full_name = (request.data.get('full_name') or '').strip()
        if not full_name:
            return Response({'error': {'detail': 'full_name is required.'}}, status=400)

        doc.signature_name = full_name
        doc.signed_at = timezone.now()
        doc.signed_ip = request.META.get('REMOTE_ADDR')
        doc.save(update_fields=['signature_name', 'signed_at', 'signed_ip'])
        return Response(GeneratedDocumentSerializer(doc).data)

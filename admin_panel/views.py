from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Agency, JurisdictionProfile, User
from accounts.permissions import IsAdmin
from accounts.serializers import AgencySerializer, JurisdictionProfileSerializer
from documents.models import GeneratedDocument
from subscriptions.models import Plan, Subscription
from subscriptions.serializers import PlanSerializer
from utils.audit_log import log_event
from utils.pagination import StandardPagination
from utils.validators import (
    ALLOWED_IMAGE_EXTENSIONS,
    EXT_TO_MIME,
    MAX_IMAGE_SIZE,
    validate_file_extension,
    validate_file_signature,
    validate_file_size,
)

from .models import AuditLog
from .serializers import (
    AdminDocumentSerializer,
    AdminGeneratedDocumentSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AuditLogSerializer,
)


class PlatformStatsView(APIView):
    """GET /api/admin-panel/stats/ — platform-wide metrics."""
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        last_30d = now - timedelta(days=30)
        last_7d = now - timedelta(days=7)
        return Response({
            'users': {
                'total': User.objects.count(),
                'officers': User.objects.filter(role='officer').count(),
                'admins': User.objects.filter(role='admin').count(),
                'active_officers': User.objects.filter(role='officer', is_active=True).count(),
                'suspended_officers': User.objects.filter(role='officer', is_active=False).count(),
                'supervisors': User.objects.filter(role='officer', is_supervisor=True).count(),
                'new_7d': User.objects.filter(created_at__gte=last_7d).count(),
            },
            'documents': {
                'total': GeneratedDocument.objects.count(),
                'last_30d': GeneratedDocument.objects.filter(created_at__gte=last_30d).count(),
                'by_type': list(
                    GeneratedDocument.objects.values('doc_type').annotate(count=Count('id'))
                ),
            },
            'subscriptions': {
                'active': Subscription.objects.filter(status='active').count(),
                'by_plan': list(
                    Subscription.objects.values('plan__name').annotate(count=Count('id'))
                ),
            },
        })


class PlanManagementView(APIView):
    """GET / POST /api/admin-panel/plans/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(PlanSerializer(Plan.objects.all(), many=True).data)

    def post(self, request):
        serializer = PlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        log_event(request.user, 'admin.plan.create', name=plan.name)
        return Response(serializer.data, status=201)


class PlanDetailView(APIView):
    """GET / PATCH / DELETE /api/admin-panel/plans/<pk>/"""
    permission_classes = [IsAdmin]

    def _get(self, pk):
        return Plan.objects.filter(pk=pk).first()

    def get(self, request, pk):
        plan = self._get(pk)
        if not plan:
            return Response({'error': {'detail': 'Plan not found.'}}, status=404)
        return Response(PlanSerializer(plan).data)

    def patch(self, request, pk):
        plan = self._get(pk)
        if not plan:
            return Response({'error': {'detail': 'Plan not found.'}}, status=404)
        serializer = PlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_event(request.user, 'admin.plan.update', name=plan.name)
        return Response(serializer.data)

    def delete(self, request, pk):
        plan = self._get(pk)
        if not plan:
            return Response({'error': {'detail': 'Plan not found.'}}, status=404)
        if plan.subscriptions.exists():
            return Response(
                {'error': {'detail': 'Cannot delete a plan with active subscriptions.'}},
                status=400,
            )
        plan_name = plan.name
        plan.delete()
        log_event(request.user, 'admin.plan.delete', severity='warning', name=plan_name)
        return Response(status=204)


class DocumentManagementView(APIView):
    """
    GET /api/admin-panel/documents/ — every officer's documents (paginated).
    Filters: ?q=<user email>, ?doc_type=, ?status=, ?review_status=,
    ?flagged=true (leak_flags/quality_flags), ?pending_review=true (shortcut
    for review_status in (pending_supervisor, pending_prosecutor) — the admin
    panel's review queue, since review_status wasn't previously surfaced or
    filterable here at all, only visible one document at a time).
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = GeneratedDocument.objects.select_related('user', 'user__agency').all()
        q = request.GET.get('q')
        if q:
            qs = qs.filter(user__email__icontains=q)
        doc_type = request.GET.get('doc_type')
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        status_f = request.GET.get('status')
        if status_f:
            qs = qs.filter(status=status_f)
        review_status_f = request.GET.get('review_status')
        if review_status_f:
            qs = qs.filter(review_status=review_status_f)
        if str(request.GET.get('pending_review', '')).lower() in ('true', '1'):
            qs = qs.filter(review_status__in=[
                GeneratedDocument.ReviewStatus.PENDING_SUPERVISOR,
                GeneratedDocument.ReviewStatus.PENDING_PROSECUTOR,
            ])
        if str(request.GET.get('flagged', '')).lower() in ('true', '1'):
            from django.db.models import Q
            qs = qs.exclude(Q(leak_flags=[]) & Q(quality_flags=[]))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AdminDocumentSerializer(page, many=True).data)


class DocumentDetailAdminView(APIView):
    """GET /api/admin-panel/documents/<pk>/ — full document (any user's)."""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        doc = GeneratedDocument.objects.select_related('user', 'user__agency').filter(pk=pk).first()
        if not doc:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)
        return Response(AdminGeneratedDocumentSerializer(doc).data)


class UserManagementView(APIView):
    """
    GET /api/admin-panel/users/ — list (paginated, searchable by ?q=).
    Filters: ?role=, ?exclude_role= (e.g. exclude_role=admin for an
    officers-only directory), ?is_active=true|false, ?is_supervisor=true|false.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = User.objects.select_related('subscription__plan', 'agency').all()
        q = request.GET.get('q')
        if q:
            qs = qs.filter(email__icontains=q)
        role = request.GET.get('role')
        if role:
            qs = qs.filter(role=role)
        exclude_role = request.GET.get('exclude_role')
        if exclude_role:
            qs = qs.exclude(role=exclude_role)
        is_active = request.GET.get('is_active')
        if is_active is not None and is_active != '':
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))
        is_supervisor = request.GET.get('is_supervisor')
        if is_supervisor is not None and is_supervisor != '':
            qs = qs.filter(is_supervisor=is_supervisor.lower() in ('true', '1'))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AdminUserSerializer(page, many=True).data)


class UserDetailView(APIView):
    """
    PATCH /api/admin-panel/users/<pk>/ — activate/deactivate, set role, plan, agency.
    Body example: {"is_active": false} or {"role": "officer"} or {"agency": 3}
    """
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response({'error': {'detail': 'User not found.'}}, status=404)

        # Update subscription plan if provided
        new_plan_name = request.data.get('plan')
        if new_plan_name:
            plan = Plan.objects.filter(name__iexact=new_plan_name).first()
            if plan:
                subscription, created = Subscription.objects.get_or_create(
                    user=user,
                    defaults={'plan': plan, 'status': 'active'}
                )
                if not created:
                    subscription.plan = plan
                    subscription.status = 'active'
                    subscription.save()
            else:
                return Response({'error': {'detail': f'Plan "{new_plan_name}" not found.'}}, status=400)

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changed = {k: v for k, v in serializer.validated_data.items()}
        if new_plan_name:
            changed['plan'] = new_plan_name
        serializer.save()
        if changed:
            log_event(request.user, 'admin.user.update', target=user.email, **changed)
        return Response(AdminUserSerializer(user).data)


class JurisdictionProfileListCreateView(APIView):
    """
    GET / POST /api/admin-panel/jurisdiction-profiles/ — shared state/federal
    defaults. Adding a new state or federal district is creating one of these,
    not writing new code (requirement #6, future scalability).
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(
            JurisdictionProfileSerializer(JurisdictionProfile.objects.all(), many=True).data
        )

    def post(self, request):
        serializer = JurisdictionProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        log_event(request.user, 'admin.jurisdiction_profile.create', name=profile.name)
        return Response(serializer.data, status=201)


class JurisdictionProfileDetailView(APIView):
    """GET / PATCH / DELETE /api/admin-panel/jurisdiction-profiles/<pk>/"""
    permission_classes = [IsAdmin]

    def _get(self, pk):
        return JurisdictionProfile.objects.filter(pk=pk).first()

    def get(self, request, pk):
        profile = self._get(pk)
        if not profile:
            return Response({'error': {'detail': 'Jurisdiction profile not found.'}}, status=404)
        return Response(JurisdictionProfileSerializer(profile).data)

    def patch(self, request, pk):
        profile = self._get(pk)
        if not profile:
            return Response({'error': {'detail': 'Jurisdiction profile not found.'}}, status=404)
        serializer = JurisdictionProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_event(request.user, 'admin.jurisdiction_profile.update', name=profile.name)
        return Response(serializer.data)

    def delete(self, request, pk):
        profile = self._get(pk)
        if not profile:
            return Response({'error': {'detail': 'Jurisdiction profile not found.'}}, status=404)
        if profile.agencies.exists():
            return Response(
                {'error': {'detail': 'Cannot delete a jurisdiction profile with agencies attached.'}},
                status=400,
            )
        if profile.warrant_templates.exists():
            return Response(
                {'error': {'detail': 'Cannot delete a jurisdiction profile with custom warrant '
                                      'templates attached. Remove or reassign its templates first.'}},
                status=400,
            )
        profile_name = profile.name
        profile.delete()
        log_event(request.user, 'admin.jurisdiction_profile.delete', severity='warning', name=profile_name)
        return Response(status=204)


class AgencyListCreateView(APIView):
    """
    GET / POST /api/admin-panel/agencies/ — agency/jurisdiction configuration.
    Admin-only: this data (court caption, judge title, prosecuting authority,
    citations) becomes printed legal text on warrants and is shared across every
    officer assigned to the agency, so it isn't self-service.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Agency.objects.select_related('jurisdiction_profile').all()
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AgencySerializer(page, many=True).data)

    def post(self, request):
        serializer = AgencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agency = serializer.save()
        log_event(request.user, 'admin.agency.create', name=agency.name)
        return Response(serializer.data, status=201)


class AgencyDetailView(APIView):
    """GET / PATCH / DELETE /api/admin-panel/agencies/<pk>/"""
    permission_classes = [IsAdmin]

    def _get(self, pk):
        return Agency.objects.filter(pk=pk).first()

    def get(self, request, pk):
        agency = self._get(pk)
        if not agency:
            return Response({'error': {'detail': 'Agency not found.'}}, status=404)
        return Response(AgencySerializer(agency).data)

    def patch(self, request, pk):
        agency = self._get(pk)
        if not agency:
            return Response({'error': {'detail': 'Agency not found.'}}, status=404)
        serializer = AgencySerializer(agency, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_event(request.user, 'admin.agency.update', name=agency.name)
        return Response(serializer.data)

    def delete(self, request, pk):
        agency = self._get(pk)
        if not agency:
            return Response({'error': {'detail': 'Agency not found.'}}, status=404)
        if agency.officers.exists():
            return Response(
                {'error': {'detail': 'Cannot delete an agency with officers assigned.'}},
                status=400,
            )
        agency_name = agency.name
        agency.delete()
        log_event(request.user, 'admin.agency.delete', severity='warning', name=agency_name)
        return Response(status=204)


class AgencySealUploadView(APIView):
    """POST /api/admin-panel/agencies/<pk>/seal/ — upload the agency seal/logo image."""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        agency = Agency.objects.filter(pk=pk).first()
        if not agency:
            return Response({'error': {'detail': 'Agency not found.'}}, status=404)

        file_obj = request.FILES.get('seal')
        if not file_obj:
            return Response({'error': {'detail': 'No "seal" file provided.'}}, status=400)

        try:
            validate_file_size(file_obj, MAX_IMAGE_SIZE)
            ext = validate_file_extension(file_obj, ALLOWED_IMAGE_EXTENSIONS)
            validate_file_signature(file_obj, EXT_TO_MIME[ext])
        except DjangoValidationError as e:
            # ValidationError.__str__ renders as a Python list repr
            # (e.g. "['File too large...']") — e.messages gives clean text.
            return Response({'error': {'detail': '; '.join(e.messages)}}, status=400)

        from utils.storage import store_upload
        key = f'agency_seals/{agency.id}{ext}'
        store_upload(file_obj, key, content_type=file_obj.content_type)
        agency.seal_image_key = key
        agency.save(update_fields=['seal_image_key'])
        log_event(request.user, 'admin.agency.seal_upload', name=agency.name)
        return Response(AgencySerializer(agency).data)


class ActivityLogView(APIView):
    """
    GET /api/admin-panel/activity/ — paginated audit trail feed backing the
    Activity Monitor. Optional ?severity=info|warning filter.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = AuditLog.objects.select_related('user').all()
        severity = request.GET.get('severity')
        if severity:
            qs = qs.filter(severity=severity)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AuditLogSerializer(page, many=True).data)

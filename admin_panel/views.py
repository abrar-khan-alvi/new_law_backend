from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdmin
from documents.models import GeneratedDocument
from documents.serializers import GeneratedDocumentSerializer
from subscriptions.models import Plan, Subscription
from subscriptions.serializers import PlanSerializer
from utils.pagination import StandardPagination

from .serializers import (
    AdminDocumentSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
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
                'verified': User.objects.filter(is_verified=True).count(),
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
        serializer.save()
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
        plan.delete()
        return Response(status=204)


class DocumentManagementView(APIView):
    """
    GET /api/admin-panel/documents/ — every officer's documents (paginated).
    Filters: ?q=<user email>, ?doc_type=, ?status=, ?flagged=true (leak_flags only).
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = GeneratedDocument.objects.select_related('user').all()
        q = request.GET.get('q')
        if q:
            qs = qs.filter(user__email__icontains=q)
        doc_type = request.GET.get('doc_type')
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        status_f = request.GET.get('status')
        if status_f:
            qs = qs.filter(status=status_f)
        if str(request.GET.get('flagged', '')).lower() in ('true', '1'):
            qs = qs.exclude(leak_flags=[])
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AdminDocumentSerializer(page, many=True).data)


class DocumentDetailAdminView(APIView):
    """GET /api/admin-panel/documents/<pk>/ — full document (any user's)."""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        doc = GeneratedDocument.objects.filter(pk=pk).first()
        if not doc:
            return Response({'error': {'detail': 'Document not found.'}}, status=404)
        return Response(GeneratedDocumentSerializer(doc).data)


class UserManagementView(APIView):
    """GET /api/admin-panel/users/ — list (paginated, searchable by ?q=)."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = User.objects.select_related('subscription__plan').all()
        q = request.GET.get('q')
        if q:
            qs = qs.filter(email__icontains=q)
        role = request.GET.get('role')
        if role:
            qs = qs.filter(role=role)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AdminUserSerializer(page, many=True).data)


class UserDetailView(APIView):
    """
    PATCH /api/admin-panel/users/<pk>/ — activate/deactivate, set role, verify.
    Body example: {"is_active": false} or {"role": "officer", "is_verified": true}
    """
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response({'error': {'detail': 'User not found.'}}, status=404)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # Stamp verification metadata when newly verifying.
        if serializer.validated_data.get('is_verified') and not user.is_verified:
            user.verified_at = timezone.now()
            user.verified_by = request.user
        serializer.save()
        return Response(AdminUserSerializer(user).data)

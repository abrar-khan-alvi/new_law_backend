from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Plan
from .serializers import PlanSerializer, SubscriptionSerializer


class PlanListView(APIView):
    """GET /api/subscriptions/plans/ — public list of active plans."""
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True)
        return Response(PlanSerializer(plans, many=True).data)


class SubscriptionStatusView(APIView):
    """GET /api/subscriptions/status/ — current user's subscription."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = getattr(request.user, 'subscription', None)
        if not sub:
            return Response({'detail': 'No subscription found.'}, status=404)
        return Response(SubscriptionSerializer(sub).data)


class CancelSubscriptionView(APIView):
    """
    POST /api/subscriptions/cancel/ — cancel the paid subscription.
    Billing actions are dormant until PAYMENTS_ENABLED; until then this is
    unavailable so we don't desync local state from Stripe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.PAYMENTS_ENABLED:
            return Response(
                {'error': {'detail': 'Billing is not enabled yet.',
                           'code': 'payments_disabled'}},
                status=503,
            )
        # Real Stripe cancellation is handled in payments (activated later).
        return Response({'message': 'Cancellation request received.'})

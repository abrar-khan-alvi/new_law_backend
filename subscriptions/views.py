from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Plan
from .serializers import PlanSerializer, SubscriptionSerializer


class PlanListView(APIView):
    """GET /api/subscriptions/plans/ — public list of active plans."""
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True).order_by('sort_order', 'price_monthly', 'id')
        return Response(PlanSerializer(plans, many=True).data)


class SubscriptionStatusView(APIView):
    """GET /api/subscriptions/status/ — current user's subscription."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = getattr(request.user, 'subscription', None)
        if not sub:
            return Response({'detail': 'No subscription found.'}, status=404)
        return Response(SubscriptionSerializer(sub).data)


class StartTrialView(APIView):
    """
    POST /api/subscriptions/start-trial/
    Legacy endpoint retained for API compatibility. New accounts automatically
    receive a 14-day Free Evaluation; extra self-started trials are disabled.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {'error': {'detail': 'Free trials are disabled. Please complete Stripe checkout to upgrade.',
                       'code': 'trials_disabled'}},
            status=403,
        )


class CancelSubscriptionView(APIView):
    """
    POST /api/subscriptions/cancel/ — cancel the paid subscription at the end
    of the current billing period (the customer keeps what they already paid
    for; Stripe's `customer.subscription.deleted` webhook then downgrades the
    local record to the free plan once the period actually ends).
    Billing actions are dormant until PAYMENTS_ENABLED; until then this is
    unavailable so we don't desync local state from Stripe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sub = getattr(request.user, 'subscription', None)
        if not sub:
            return Response(
                {'error': {'detail': 'No paid subscription to cancel.', 'code': 'no_paid_subscription'}},
                status=400,
            )

        # A trial never touches Stripe by design, so it has no
        # stripe_subscription_id to cancel — revert to Free immediately
        # instead of waiting out the remaining trial days. Purely local
        # state, so this doesn't need PAYMENTS_ENABLED/Stripe at all.
        if sub.status == 'trialing':
            free_plan = Plan.objects.filter(name='free').first()
            if not free_plan:
                return Response(
                    {'error': {'detail': 'No free plan configured.', 'code': 'no_free_plan'}}, status=500)
            sub.plan = free_plan
            sub.status = 'expired'
            sub.documents_generated_this_month = 0
            sub.warrants_generated_this_month = 0
            sub.search_warrants_generated_this_month = 0
            sub.arrest_warrants_generated_this_month = 0
            sub.usage_reset_date = timezone.now().date()
            sub.save(update_fields=[
                'plan', 'status', 'documents_generated_this_month',
                'warrants_generated_this_month', 'search_warrants_generated_this_month',
                'arrest_warrants_generated_this_month', 'usage_reset_date',
            ])
            return Response({'message': 'Your free evaluation has ended. Choose a paid plan to continue.'})

        if not settings.PAYMENTS_ENABLED:
            return Response(
                {'error': {'detail': 'Billing is not enabled yet.',
                           'code': 'payments_disabled'}},
                status=503,
            )

        if not sub.stripe_subscription_id:
            return Response(
                {'error': {'detail': 'No paid subscription to cancel.', 'code': 'no_paid_subscription'}},
                status=400,
            )
        if sub.cancel_at_period_end:
            return Response({'message': 'Cancellation already scheduled.',
                              'current_period_end': sub.current_period_end})

        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
        except stripe.error.StripeError as e:
            return Response(
                {'error': {'detail': f'Stripe cancellation failed: {e}', 'code': 'stripe_error'}},
                status=502,
            )

        sub.cancel_at_period_end = True
        sub.cancelled_at = timezone.now()
        sub.save(update_fields=['cancel_at_period_end', 'cancelled_at'])
        return Response({
            'message': 'Your subscription will not renew and will end on your current billing date.',
            'current_period_end': sub.current_period_end,
        })

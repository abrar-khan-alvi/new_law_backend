from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Plan
from .serializers import PlanSerializer, SubscriptionSerializer

TRIAL_DAYS = 14


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


class StartTrialView(APIView):
    """
    POST /api/subscriptions/start-trial/
    Body: {"plan": "standard"|"pro"}
    A single no-card-required trial per account, available only from the free
    plan. Reverts to free automatically after TRIAL_DAYS (see
    subscriptions.tasks.expire_trials, run daily by Celery beat) unless the
    user checks out for real before then.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sub = getattr(request.user, 'subscription', None)
        if not sub:
            return Response({'error': {'detail': 'No subscription found.'}}, status=404)
        if sub.has_used_trial:
            return Response(
                {'error': {'detail': 'You have already used your free trial.', 'code': 'trial_used'}},
                status=400,
            )
        if sub.plan.name != 'free':
            return Response(
                {'error': {'detail': 'A trial is only available from the Free plan.', 'code': 'not_on_free'}},
                status=400,
            )

        plan_name = request.data.get('plan')
        plan = Plan.objects.filter(name=plan_name, is_active=True).exclude(name='free').first()
        if not plan:
            return Response({'error': {'detail': 'Unknown plan.'}}, status=400)

        sub.plan = plan
        sub.status = 'trialing'
        sub.trial_end = timezone.now() + timedelta(days=TRIAL_DAYS)
        sub.has_used_trial = True
        sub.documents_generated_this_month = 0
        sub.save(update_fields=[
            'plan', 'status', 'trial_end', 'has_used_trial', 'documents_generated_this_month',
        ])
        return Response(SubscriptionSerializer(sub).data, status=201)


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
        if not settings.PAYMENTS_ENABLED:
            return Response(
                {'error': {'detail': 'Billing is not enabled yet.',
                           'code': 'payments_disabled'}},
                status=503,
            )

        sub = getattr(request.user, 'subscription', None)
        if not sub or not sub.stripe_subscription_id:
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

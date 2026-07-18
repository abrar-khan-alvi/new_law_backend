from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.models import Plan
from subscriptions.serializers import SubscriptionSerializer

from .models import Invoice, Payment
from .webhooks import _ts, handle_webhook


def _disabled_response():
    from rest_framework import status
    return Response(
        {'error': {'detail': 'Payments are not enabled yet.', 'code': 'payments_disabled'}},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class CreateCheckoutSessionView(APIView):
    """
    POST /api/payments/create-checkout/
    Body: {"plan": "pro", "billing_period": "monthly"}
    Dormant until PAYMENTS_ENABLED. Price IDs are read from
    Plan.stripe_price_id_monthly/yearly (admin-editable), not a hardcoded
    settings mapping — see subscriptions/models.py.

    If the user already has a live Stripe subscription, this changes that
    subscription's price in place (prorated) instead of starting a second one
    — previously, upgrading without cancelling first would leave a customer
    with two active subscriptions billing simultaneously. A brand-new Stripe
    Checkout Session is only created for someone still on Free (or whose prior
    subscription has actually ended — see _on_subscription_cancelled, which
    clears stripe_subscription_id once Stripe confirms cancellation).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.PAYMENTS_ENABLED:
            return _disabled_response()

        period = request.data.get('billing_period', 'monthly')
        if period not in ('monthly', 'yearly'):
            return Response({'error': {'detail': 'billing_period must be "monthly" or "yearly".'}}, status=400)

        plan_name = request.data.get('plan')
        plan = Plan.objects.filter(name=plan_name, is_active=True).exclude(name='free').first()
        if not plan:
            return Response({'error': {'detail': 'Unknown plan.'}}, status=400)

        price_id = plan.stripe_price_id_monthly if period == 'monthly' else plan.stripe_price_id_yearly
        if not price_id:
            return Response(
                {'error': {'detail': f'{plan.display_name} has no Stripe price configured for {period} billing.',
                           'code': 'plan_not_configured'}},
                status=400,
            )

        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        sub = getattr(request.user, 'subscription', None)
        if sub and sub.stripe_subscription_id:
            return self._change_existing_subscription(sub, plan, period, price_id, stripe)

        session = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=f'{settings.FRONTEND_URL}/billing/success',
            cancel_url=f'{settings.FRONTEND_URL}/billing/cancel',
            customer_email=request.user.email,
            metadata={'user_id': str(request.user.id), 'plan': plan.name, 'billing_period': period},
        )
        return Response({'checkout_url': session.url, 'session_id': session.id})

    def _change_existing_subscription(self, sub, plan, period, price_id, stripe):
        try:
            stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
            item_id = stripe_sub['items']['data'][0]['id']
            updated = stripe.Subscription.modify(
                sub.stripe_subscription_id,
                items=[{'id': item_id, 'price': price_id}],
                proration_behavior='create_prorations',
                cancel_at_period_end=False,
            )
        except stripe.error.StripeError as e:
            return Response(
                {'error': {'detail': f'Stripe plan change failed: {e}', 'code': 'stripe_error'}},
                status=502,
            )

        sub.plan = plan
        sub.billing_period = period
        sub.status = 'active'
        sub.cancel_at_period_end = False
        sub.current_period_start = _ts(updated['current_period_start'])
        sub.current_period_end = _ts(updated['current_period_end'])
        sub.save()
        return Response({
            'message': f'Plan changed to {plan.display_name}.',
            'subscription': SubscriptionSerializer(sub).data,
        })


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """POST /api/payments/webhook/ — Stripe event receiver. Dormant until enabled."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not settings.PAYMENTS_ENABLED:
            return _disabled_response()
        sig = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        try:
            handle_webhook(request.body, sig)
        except ValueError as e:
            return Response({'error': {'detail': str(e)}}, status=400)
        return Response({'received': True})


class BillingHistoryView(APIView):
    """GET /api/payments/billing-history/ — current user's payments + invoices."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(user=request.user).values(
            'id', 'amount', 'currency', 'status', 'description', 'created_at')
        invoices = Invoice.objects.filter(user=request.user).values(
            'id', 'amount_due', 'amount_paid', 'currency', 'status',
            'hosted_invoice_url', 'invoice_pdf', 'created_at')
        return Response({'payments': list(payments), 'invoices': list(invoices)})

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invoice, Payment
from .webhooks import handle_webhook


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
    Creates a Stripe Checkout Session. Dormant until PAYMENTS_ENABLED.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.PAYMENTS_ENABLED:
            return _disabled_response()

        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        plan = request.data.get('plan')
        period = request.data.get('billing_period', 'monthly')
        price_id = settings.STRIPE_PRICES.get((plan, period))
        if not price_id:
            return Response({'error': {'detail': 'Unknown plan/period.'}}, status=400)

        session = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=f'{settings.FRONTEND_URL}/billing/success',
            cancel_url=f'{settings.FRONTEND_URL}/billing/cancel',
            customer_email=request.user.email,
            metadata={'user_id': str(request.user.id)},
        )
        return Response({'checkout_url': session.url, 'session_id': session.id})


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

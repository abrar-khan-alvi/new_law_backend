"""
Regression tests for the Stripe webhook fixes:
- Payment/Invoice rows are actually created on invoice.payment_succeeded
  (previously dead code — the models existed but nothing wrote to them).
- Webhook events are deduplicated by Stripe event ID, so a retried delivery
  (Stripe retries on any non-2xx/slow response) can't be reprocessed — e.g.
  re-zeroing documents_generated_this_month for free on a replayed
  checkout.session.completed.
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from payments.models import Invoice, Payment, WebhookEvent
from payments.webhooks import handle_webhook
from subscriptions.models import Plan, Subscription

User = get_user_model()


def _checkout_event(event_id, user_id, price_id):
    return {
        'id': event_id,
        'type': 'checkout.session.completed',
        'data': {'object': {
            'metadata': {'user_id': str(user_id)},
            'subscription': 'sub_123',
        }},
    }


def _invoice_event(event_id, customer_id, invoice_id='in_1', payment_intent='pi_1'):
    return {
        'id': event_id,
        'type': 'invoice.payment_succeeded',
        'data': {'object': {
            'id': invoice_id,
            'customer': customer_id,
            'amount_due': 2999,
            'amount_paid': 2999,
            'currency': 'usd',
            'status': 'paid',
            'period_start': 1750000000,
            'period_end': 1752600000,
            'hosted_invoice_url': 'https://stripe.example/invoice',
            'invoice_pdf': 'https://stripe.example/invoice.pdf',
            'payment_intent': payment_intent,
            'charge': 'ch_1',
            'number': 'INV-0001',
            'customer_email': 'billing@example.com',
        }},
    }


class WebhookIdempotencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='webhook-user@example.com', role='officer')
        self.plan = Plan.objects.create(
            name='t-pro', display_name='Pro',
            stripe_price_id_monthly='price_pro_monthly',
        )
        Subscription.objects.filter(user=self.user).delete()
        self.sub = Subscription.objects.create(
            user=self.user, plan=Plan.objects.create(name='free-w', display_name='Free'),
            status='active', documents_generated_this_month=3,
        )

    @patch('stripe.Subscription.retrieve')
    @patch('stripe.Webhook.construct_event')
    def test_replayed_checkout_event_does_not_reprocess(self, mock_construct, mock_retrieve):
        event = _checkout_event('evt_dup_1', self.user.id, 'price_pro_monthly')
        mock_construct.return_value = event
        mock_retrieve.return_value = {
            'id': 'sub_123', 'customer': 'cus_1',
            'items': {'data': [{'price': {'id': 'price_pro_monthly'}}]},
            'current_period_start': 1750000000, 'current_period_end': 1752600000,
        }

        handle_webhook(b'payload', 'sig')
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan_id, self.plan.id)
        self.assertEqual(WebhookEvent.objects.count(), 1)

        # Simulate Stripe redelivering the identical event (e.g. after a slow
        # 200 response) — usage was bumped back up in between; a naive
        # re-handle would zero it out again for free.
        self.sub.documents_generated_this_month = 5
        self.sub.save(update_fields=['documents_generated_this_month'])

        handle_webhook(b'payload', 'sig')

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 5)  # untouched by the replay
        self.assertEqual(WebhookEvent.objects.count(), 1)  # no second row


class PaymentInvoiceWiringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='invoice-user@example.com', role='officer')
        Subscription.objects.filter(user=self.user).delete()
        self.sub = Subscription.objects.create(
            user=self.user, plan=Plan.objects.create(name='free-i', display_name='Free'),
            stripe_customer_id='cus_42',
        )

    @patch('stripe.Webhook.construct_event')
    def test_invoice_payment_succeeded_creates_invoice_and_payment(self, mock_construct):
        mock_construct.return_value = _invoice_event('evt_inv_1', 'cus_42')

        handle_webhook(b'payload', 'sig')

        invoice = Invoice.objects.get(stripe_invoice_id='in_1')
        self.assertEqual(invoice.user, self.user)
        self.assertEqual(str(invoice.amount_paid), '29.99')

        payment = Payment.objects.get(stripe_payment_intent_id='pi_1')
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.status, Payment.Status.SUCCEEDED)

    @patch('stripe.Webhook.construct_event')
    def test_unknown_customer_does_not_crash(self, mock_construct):
        mock_construct.return_value = _invoice_event('evt_inv_2', 'cus_does_not_exist')
        handle_webhook(b'payload', 'sig')  # must not raise
        self.assertFalse(Invoice.objects.filter(stripe_invoice_id='in_1').exists())

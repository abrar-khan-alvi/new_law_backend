"""
Stripe webhook event handling.

Dormant until PAYMENTS_ENABLED (a Stripe key is configured). The handlers are
written and ready; they are only invoked by StripeWebhookView, which refuses
requests while payments are disabled.
"""
import logging
from datetime import datetime, timezone

from django.conf import settings

from accounts.models import User
from subscriptions.models import Subscription, Plan

logger = logging.getLogger(__name__)


def _price_to_plan():
    """Invert STRIPE_PRICES → {price_id: (plan_name, period)} (skip empties)."""
    return {
        price_id: (name, period)
        for (name, period), price_id in settings.STRIPE_PRICES.items()
        if price_id
    }


def _ts(unix):
    return datetime.fromtimestamp(unix, tz=timezone.utc) if unix else None


def handle_webhook(payload: bytes, sig_header: str):
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as exc:
        raise ValueError('Invalid Stripe signature.') from exc

    handler = {
        'checkout.session.completed': _on_checkout_complete,
        'customer.subscription.updated': _on_subscription_updated,
        'customer.subscription.deleted': _on_subscription_cancelled,
        'invoice.payment_succeeded': _on_payment_succeeded,
        'invoice.payment_failed': _on_payment_failed,
    }.get(event['type'])

    if handler:
        handler(event['data']['object'])
    else:
        logger.info('Unhandled Stripe event: %s', event['type'])


def _on_checkout_complete(session):
    import stripe
    user_id = (session.get('metadata') or {}).get('user_id')
    stripe_sub = stripe.Subscription.retrieve(session['subscription'])
    price_id = stripe_sub['items']['data'][0]['price']['id']
    plan_name, period = _price_to_plan().get(price_id, ('basic', 'monthly'))

    try:
        user = User.objects.get(pk=user_id)
        sub = user.subscription
        sub.plan = Plan.objects.get(name=plan_name)
        sub.status = 'active'
        sub.billing_period = period
        sub.stripe_subscription_id = stripe_sub['id']
        sub.stripe_customer_id = stripe_sub['customer']
        sub.current_period_start = _ts(stripe_sub['current_period_start'])
        sub.current_period_end = _ts(stripe_sub['current_period_end'])
        sub.documents_generated_this_month = 0
        sub.save()
        logger.info('Subscription activated: %s → %s', user.email, plan_name)
    except User.DoesNotExist:
        logger.error('Checkout complete but user %s not found.', user_id)


def _on_subscription_updated(stripe_sub):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        sub.status = stripe_sub['status']
        sub.current_period_start = _ts(stripe_sub['current_period_start'])
        sub.current_period_end = _ts(stripe_sub['current_period_end'])
        sub.save(update_fields=['status', 'current_period_start', 'current_period_end'])
    except Subscription.DoesNotExist:
        pass


def _on_subscription_cancelled(stripe_sub):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        sub.plan = Plan.objects.get(name='free')
        sub.status = 'cancelled'
        sub.save(update_fields=['plan', 'status'])
        logger.info('Subscription cancelled: %s', sub.user.email)
    except (Subscription.DoesNotExist, Plan.DoesNotExist):
        pass


def _on_payment_succeeded(invoice):
    logger.info('Payment succeeded: %s', invoice.get('customer_email'))


def _on_payment_failed(invoice):
    try:
        sub = Subscription.objects.get(stripe_customer_id=invoice['customer'])
        sub.status = 'past_due'
        sub.save(update_fields=['status'])
        logger.warning('Payment failed: %s', invoice.get('customer_email'))
    except Subscription.DoesNotExist:
        pass

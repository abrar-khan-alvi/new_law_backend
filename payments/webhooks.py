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
    """
    {price_id: (plan_name, period)}, built from the Plan table itself — the
    same source of truth CreateCheckoutSessionView reads from — rather than a
    hardcoded settings dict that has to be kept in sync by hand.
    """
    mapping = {}
    for plan in Plan.objects.filter(is_active=True):
        if plan.stripe_price_id_monthly:
            mapping[plan.stripe_price_id_monthly] = (plan.name, 'monthly')
        if plan.stripe_price_id_yearly:
            mapping[plan.stripe_price_id_yearly] = (plan.name, 'yearly')
    return mapping


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
    resolved = _price_to_plan().get(price_id)
    if not resolved:
        # Unrecognized price ID — no Plan row has this price ID configured.
        # Fail loudly rather than silently guessing a plan the customer didn't
        # pay for; an admin needs to set the right Plan.stripe_price_id_* field.
        logger.error(
            'Checkout complete with unrecognized Stripe price_id=%s (user_id=%s) — '
            'no active Plan has this price ID set. Subscription NOT activated.',
            price_id, user_id,
        )
        return
    plan_name, period = resolved

    try:
        user = User.objects.get(pk=user_id)
        plan = Plan.objects.get(name=plan_name)
    except User.DoesNotExist:
        logger.error('Checkout complete but user %s not found.', user_id)
        return
    except Plan.DoesNotExist:
        logger.error(
            'Checkout complete for plan "%s" (user %s) but that plan no longer exists.',
            plan_name, user_id,
        )
        return

    sub = user.subscription
    sub.plan = plan
    sub.status = 'active'
    sub.billing_period = period
    sub.stripe_subscription_id = stripe_sub['id']
    sub.stripe_customer_id = stripe_sub['customer']
    sub.current_period_start = _ts(stripe_sub['current_period_start'])
    sub.current_period_end = _ts(stripe_sub['current_period_end'])
    sub.documents_generated_this_month = 0
    sub.warrants_generated_this_month = 0
    sub.cancel_at_period_end = False
    sub.save()
    logger.info('Subscription activated: %s → %s', user.email, plan_name)


def _on_subscription_updated(stripe_sub):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        sub.status = stripe_sub['status']
        sub.current_period_start = _ts(stripe_sub['current_period_start'])
        sub.current_period_end = _ts(stripe_sub['current_period_end'])
        sub.cancel_at_period_end = bool(stripe_sub.get('cancel_at_period_end'))
        sub.save(update_fields=[
            'status', 'current_period_start', 'current_period_end', 'cancel_at_period_end',
        ])
    except Subscription.DoesNotExist:
        pass


def _on_subscription_cancelled(stripe_sub):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        sub.plan = Plan.objects.get(name='free')
        sub.status = 'cancelled'
        sub.cancel_at_period_end = False
        # Clear it — otherwise a future resubscribe attempt would try to
        # modify this now-dead Stripe subscription instead of starting a new one.
        sub.stripe_subscription_id = ''
        sub.save(update_fields=['plan', 'status', 'cancel_at_period_end', 'stripe_subscription_id'])
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

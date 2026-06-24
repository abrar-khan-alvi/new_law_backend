import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
def create_free_subscription(sender, instance, created, **kwargs):
    """
    Give every new user a free subscription on creation, so quota/feature
    checks always have a Subscription to read.
    """
    if not created:
        return

    # Imported lazily to avoid app-loading order issues.
    from subscriptions.models import Plan, Subscription

    if hasattr(instance, 'subscription'):
        return

    # Pick the lowest priced active plan instead of hardcoding 'free'
    free_plan = Plan.objects.filter(is_active=True).order_by('price_monthly').first()
    if not free_plan:
        logger.warning("No active plans found to assign as default.")
        return

    Subscription.objects.create(user=instance, plan=free_plan, status='active')
    logger.info("Free subscription created for %s", instance.email)

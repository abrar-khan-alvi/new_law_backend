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

    free_plan = Plan.objects.filter(name='free').first()
    if not free_plan:
        logger.warning("No 'free' plan found — run `manage.py seed_plans`.")
        return

    Subscription.objects.create(user=instance, plan=free_plan, status='active')
    logger.info("Free subscription created for %s", instance.email)

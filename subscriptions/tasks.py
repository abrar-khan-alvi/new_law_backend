from celery import shared_task
from django.utils import timezone

from .models import Plan, Subscription


@shared_task
def reset_monthly_usage():
    """Reset monthly counters for active paid subscriptions."""
    count = 0
    for sub in Subscription.objects.filter(status=Subscription.Status.ACTIVE):
        sub.reset_monthly_usage()
        count += 1
    return f'Reset usage for {count} subscriptions.'


@shared_task
def expire_trials():
    """Mark expired Free Evaluations as expired instead of reactivating Free."""
    free_plan = Plan.objects.filter(name='free').first()
    if not free_plan:
        return 'No free plan configured - skipped.'

    expired = Subscription.objects.filter(
        status=Subscription.Status.TRIALING,
        plan=free_plan,
        trial_end__lt=timezone.now(),
    )
    count = 0
    for sub in expired:
        sub.status = Subscription.Status.EXPIRED
        sub.usage_reset_date = timezone.now().date()
        sub.save(update_fields=['status', 'usage_reset_date'])
        count += 1
    return f'Expired {count} free evaluation(s).'

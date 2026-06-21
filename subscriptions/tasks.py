from celery import shared_task

from .models import Subscription


@shared_task
def reset_monthly_usage():
    """Reset the monthly document counter for all active subscriptions."""
    count = 0
    for sub in Subscription.objects.filter(status='active'):
        sub.reset_monthly_usage()
        count += 1
    return f'Reset usage for {count} subscriptions.'

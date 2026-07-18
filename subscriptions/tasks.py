from celery import shared_task
from django.utils import timezone

from .models import Plan, Subscription


@shared_task
def reset_monthly_usage():
    """Reset the monthly document counter for all active subscriptions."""
    count = 0
    for sub in Subscription.objects.filter(status='active'):
        sub.reset_monthly_usage()
        count += 1
    return f'Reset usage for {count} subscriptions.'


@shared_task
def expire_trials():
    """Revert any trial whose trial_end has passed back to the free plan."""
    free_plan = Plan.objects.filter(name='free').first()
    if not free_plan:
        return 'No free plan configured — skipped.'

    expired = Subscription.objects.filter(status='trialing', trial_end__lt=timezone.now())
    count = 0
    for sub in expired:
        sub.plan = free_plan
        sub.status = 'active'
        sub.trial_end = None
        # Reset usage — otherwise someone who generated well past Free's small
        # quota during a Pro trial would land back on Free already over-limit
        # and be locked out until next month's reset, through no fault of theirs.
        sub.documents_generated_this_month = 0
        sub.save(update_fields=['plan', 'status', 'trial_end', 'documents_generated_this_month'])
        count += 1
    return f'Expired {count} trial(s).'

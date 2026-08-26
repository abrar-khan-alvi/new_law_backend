import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from subscriptions.models import Plan, Subscription

# document_limit=None means unlimited (a real nullable field, not a sentinel).
#
# Stripe price IDs: Plan.stripe_price_id_monthly/yearly in the database is the
# live source of truth for checkout (admin-editable via the admin panel, no
# redeploy needed) — there is no separate settings dict to keep in sync. The
# STRIPE_PRICE_* env vars below are read only as a one-time bootstrap default:
# if a plan doesn't have a price ID yet, seed it from the environment; if an
# admin has since edited it in the DB, this command leaves that edit alone.


def _bootstrap_price(existing_plans: dict, name: str, field: str, env_var: str) -> str:
    plan = existing_plans.get(name)
    if plan and getattr(plan, field):
        return getattr(plan, field)
    return os.environ.get(env_var, '')


def _default_plans() -> list:
    existing = {p.name: p for p in Plan.objects.all()}
    return [
        {
            'name': 'free',
            'display_name': 'Free Evaluation',
            'description': ('Evaluate KLYVOREK for 14 days with 10 total document generations. '
                            'No credit card required. Incident reports, search warrants, arrest '
                            'warrants, PDF export, and editable DOCX export are included.'),
            'price_monthly': 0, 'price_yearly': 0,
            'document_limit': 10,
            'warrant_document_limit': 10,
            'can_incident_report': True,
            'can_search_warrant': True,
            'can_arrest_warrant': True,
            'can_export_pdf': True,
            'can_export_docx': True,
            'can_save_history': True,
            'support_level': 'community',
            'is_active': True,
            'sort_order': 0,
        },
        {
            'name': 'standard',
            'display_name': 'Plus',
            'description': ('For individual officers. 50 incident reports per month, 10 search or '
                            'arrest warrant drafts per month, and editable DOCX export.'),
            'price_monthly': 29, 'price_yearly': 290,
            'stripe_price_id_monthly': _bootstrap_price(existing, 'standard', 'stripe_price_id_monthly', 'STRIPE_PRICE_STANDARD_MONTHLY'),
            'stripe_price_id_yearly': _bootstrap_price(existing, 'standard', 'stripe_price_id_yearly', 'STRIPE_PRICE_STANDARD_YEARLY'),
            'document_limit': 50,
            'warrant_document_limit': 10,
            'can_incident_report': True,
            'can_search_warrant': True,
            'can_arrest_warrant': True,
            'can_export_pdf': True,
            'can_export_docx': True,
            'can_save_history': True,
            'support_level': 'email',
            'is_active': True,
            'sort_order': 1,
        },
        {
            'name': 'pro',
            'display_name': 'Pro',
            'description': ('Unlimited access for high-volume users. Unlimited incident reports, '
                            'search warrants, and arrest warrants — plus priority support.'),
            'price_monthly': 59, 'price_yearly': 590,
            'stripe_price_id_monthly': _bootstrap_price(existing, 'pro', 'stripe_price_id_monthly', 'STRIPE_PRICE_PRO_MONTHLY'),
            'stripe_price_id_yearly': _bootstrap_price(existing, 'pro', 'stripe_price_id_yearly', 'STRIPE_PRICE_PRO_YEARLY'),
            'document_limit': None,
            'warrant_document_limit': None,
            'can_incident_report': True,
            'can_search_warrant': True,
            'can_arrest_warrant': True,
            'can_export_pdf': True,
            'can_export_docx': True,
            'can_save_history': True,
            'support_level': 'priority',
            'is_active': True,
            'sort_order': 2,
        },
    ]


class Command(BaseCommand):
    help = 'Create or update the default subscription plans (idempotent).'

    def handle(self, *args, **options):
        default_plans = _default_plans()
        names = [data['name'] for data in default_plans]
        created, updated = 0, 0
        for data in default_plans:
            _, was_created = Plan.objects.update_or_create(name=data['name'], defaults=data)
            created += int(was_created)
            updated += int(not was_created)

        # Retire any plan no longer offered (e.g. old basic/enterprise). Deactivate
        # rather than delete so existing subscriptions referencing them stay intact.
        retired = Plan.objects.exclude(name__in=names).filter(is_active=True)
        retired_count = retired.update(is_active=False)
        free_plan = Plan.objects.filter(name='free').first()
        transitioned_count = 0
        if free_plan:
            transitioned_count = Subscription.objects.filter(
                plan=free_plan,
                status=Subscription.Status.ACTIVE,
                stripe_subscription_id='',
                trial_end__isnull=True,
            ).update(
                status=Subscription.Status.TRIALING,
                trial_end=timezone.now() + timedelta(days=14),
                has_used_trial=True,
                usage_reset_date=timezone.now().date(),
            )

        self.stdout.write(self.style.SUCCESS(
            f'Plans seeded — {created} created, {updated} updated, {retired_count} retired.'
        ))

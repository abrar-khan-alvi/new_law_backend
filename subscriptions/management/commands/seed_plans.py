from django.core.management.base import BaseCommand

from subscriptions.models import Plan

# Unlimited document quota is modeled as a high sentinel (the field is an integer).
UNLIMITED = 1_000_000

# Three per-officer, self-serve tiers. Admins can edit prices/limits/Stripe IDs
# later in Django admin / the admin panel — these are sensible starting values.
DEFAULT_PLANS = [
    {
        'name': 'free',
        'display_name': 'Free',
        'description': 'Try the platform — incident reports with PDF export, 5 documents per month.',
        'price_monthly': 0, 'price_yearly': 0,
        'document_limit': 5,
        'can_incident_report': True,
        'can_search_warrant': False,
        'can_arrest_warrant': False,
        'can_export_pdf': True,
        'can_export_docx': False,
        'can_save_history': True,
        'can_regenerate': False,
        'support_level': 'community',
        'is_active': True,
        'sort_order': 0,
    },
    {
        'name': 'standard',
        'display_name': 'Standard',
        'description': ('All document types (incident reports, search & arrest warrants) '
                        'with editable DOCX export and regeneration. 50 documents per month.'),
        'price_monthly': 29, 'price_yearly': 290,
        'document_limit': 50,
        'can_incident_report': True,
        'can_search_warrant': True,
        'can_arrest_warrant': True,
        'can_export_pdf': True,
        'can_export_docx': True,
        'can_save_history': True,
        'can_regenerate': True,
        'support_level': 'email',
        'is_active': True,
        'sort_order': 1,
    },
    {
        'name': 'pro',
        'display_name': 'Pro',
        'description': ('Everything in Standard with unlimited documents and priority support '
                        'for power users.'),
        'price_monthly': 59, 'price_yearly': 590,
        'document_limit': UNLIMITED,
        'can_incident_report': True,
        'can_search_warrant': True,
        'can_arrest_warrant': True,
        'can_export_pdf': True,
        'can_export_docx': True,
        'can_save_history': True,
        'can_regenerate': True,
        'support_level': 'priority',
        'is_active': True,
        'sort_order': 2,
    },
]


class Command(BaseCommand):
    help = 'Create or update the default subscription plans (idempotent).'

    def handle(self, *args, **options):
        names = [data['name'] for data in DEFAULT_PLANS]
        created, updated = 0, 0
        for data in DEFAULT_PLANS:
            _, was_created = Plan.objects.update_or_create(name=data['name'], defaults=data)
            created += int(was_created)
            updated += int(not was_created)

        # Retire any plan no longer offered (e.g. old basic/enterprise). Deactivate
        # rather than delete so existing subscriptions referencing them stay intact.
        retired = Plan.objects.exclude(name__in=names).filter(is_active=True)
        retired_count = retired.update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Plans seeded — {created} created, {updated} updated, {retired_count} retired.'
        ))

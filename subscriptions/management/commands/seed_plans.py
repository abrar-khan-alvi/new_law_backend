from django.core.management.base import BaseCommand

from subscriptions.models import Plan

# Default plan tiers. Admins can edit prices, limits, and Stripe IDs later
# in Django admin / the admin panel — these are just sensible starting values.
DEFAULT_PLANS = [
    {
        'name': 'free',
        'display_name': 'Free',
        'description': 'Preview the platform. Limited document generation.',
        'price_monthly': 0, 'price_yearly': 0,
        'document_limit': 3,
        'can_incident_report': True,
        'can_search_warrant': False,
        'can_arrest_warrant': False,
        'can_export_pdf': True,
        'can_export_docx': False,
        'can_save_history': False,
        'can_regenerate': False,
        'support_level': 'community',
        'sort_order': 0,
    },
    {
        'name': 'basic',
        'display_name': 'Basic',
        'description': 'Incident reports and search warrants for individual officers.',
        'price_monthly': 29, 'price_yearly': 290,
        'document_limit': 25,
        'can_incident_report': True,
        'can_search_warrant': True,
        'can_arrest_warrant': False,
        'can_export_pdf': True,
        'can_export_docx': True,
        'can_save_history': True,
        'can_regenerate': True,
        'support_level': 'email',
        'sort_order': 1,
    },
    {
        'name': 'pro',
        'display_name': 'Pro',
        'description': 'All document modules with full export and history.',
        'price_monthly': 79, 'price_yearly': 790,
        'document_limit': 100,
        'can_incident_report': True,
        'can_search_warrant': True,
        'can_arrest_warrant': True,
        'can_export_pdf': True,
        'can_export_docx': True,
        'can_save_history': True,
        'can_regenerate': True,
        'support_level': 'priority',
        'sort_order': 2,
    },
    {
        'name': 'enterprise',
        'display_name': 'Enterprise',
        'description': 'High-volume access for agencies.',
        'price_monthly': 299, 'price_yearly': 2990,
        'document_limit': 1000,
        'can_incident_report': True,
        'can_search_warrant': True,
        'can_arrest_warrant': True,
        'can_export_pdf': True,
        'can_export_docx': True,
        'can_save_history': True,
        'can_regenerate': True,
        'support_level': 'priority',
        'sort_order': 3,
    },
]


class Command(BaseCommand):
    help = 'Create or update the default subscription plans (idempotent).'

    def handle(self, *args, **options):
        created, updated = 0, 0
        for data in DEFAULT_PLANS:
            obj, was_created = Plan.objects.update_or_create(
                name=data['name'], defaults=data,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Plans seeded — {created} created, {updated} updated.'
        ))

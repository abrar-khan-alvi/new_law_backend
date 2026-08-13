from django.db import migrations, models


def configure_free_lifetime_plan(apps, schema_editor):
    Plan = apps.get_model('subscriptions', 'Plan')
    Plan.objects.filter(name='free').update(
        description=(
            'Seven AI document generations for the lifetime of the account, combined across '
            'incident reports, search warrants, and arrest warrants. PDF and DOCX test exports included.'
        ),
        document_limit=7,
        warrant_document_limit=7,
        can_incident_report=True,
        can_search_warrant=True,
        can_arrest_warrant=True,
        can_export_pdf=True,
        can_export_docx=True,
        can_save_history=True,
    )


class Migration(migrations.Migration):
    dependencies = [('subscriptions', '0004_subscription_arrest_warrants_generated_this_month_and_more')]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='document_limit',
            field=models.PositiveIntegerField(
                blank=True,
                default=7,
                help_text='Incident reports per month (the Free plan uses this as a combined lifetime limit). Leave blank for unlimited.',
                null=True,
            ),
        ),
        migrations.RunPython(configure_free_lifetime_plan, migrations.RunPython.noop),
    ]

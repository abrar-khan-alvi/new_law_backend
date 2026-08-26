from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_alter_plan_document_limit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='document_limit',
            field=models.PositiveIntegerField(
                blank=True,
                default=10,
                help_text='Incident reports per month (the Free Evaluation plan uses this as a combined trial limit). Leave blank for unlimited.',
                null=True,
            ),
        ),
    ]

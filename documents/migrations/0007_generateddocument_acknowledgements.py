from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('documents', '0006_warranttemplate_uniqueness_constraints')]

    operations = [
        migrations.AddField(
            model_name='generateddocument', name='source_acknowledged_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='generateddocument', name='review_acknowledged_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='generateddocument', name='review_acknowledged_content_hash',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]

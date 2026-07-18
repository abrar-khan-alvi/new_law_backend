from django.db import migrations


def seed_templates(apps, schema_editor):
    WarrantTemplate = apps.get_model('documents', 'WarrantTemplate')
    # Imported here (not at module level) so this migration keeps working even
    # if the template content module changes shape later.
    from documents.templates_engine import DEFAULT_TEMPLATES

    for doc_type, by_jurisdiction in DEFAULT_TEMPLATES.items():
        for jurisdiction_type, sections in by_jurisdiction.items():
            for section_key, template_text in sections.items():
                WarrantTemplate.objects.get_or_create(
                    agency=None, jurisdiction_profile=None,
                    doc_type=doc_type, section_key=section_key, jurisdiction_type=jurisdiction_type,
                    defaults={'template_text': template_text},
                )


def unseed_templates(apps, schema_editor):
    WarrantTemplate = apps.get_model('documents', 'WarrantTemplate')
    WarrantTemplate.objects.filter(agency=None, jurisdiction_profile=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_generateddocument_narrative_body_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]

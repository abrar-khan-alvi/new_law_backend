from django.contrib import admin

from .models import GeneratedDocument, WarrantTemplate


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'doc_type', 'case_number', 'status',
        'narrative_style', 'review_status', 'created_at',
    )
    list_filter = ('doc_type', 'status', 'narrative_style', 'review_status')
    search_fields = ('case_number', 'user__email')
    raw_id_fields = ('user', 'supervisor_reviewed_by')
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'model_used',
        'tokens_used', 'generation_time_ms',
    )


@admin.register(WarrantTemplate)
class WarrantTemplateAdmin(admin.ModelAdmin):
    list_display = ('doc_type', 'section_key', 'agency', 'jurisdiction_profile', 'updated_at')
    list_filter = ('doc_type', 'section_key')
    search_fields = ('agency__name', 'jurisdiction_profile__name')
    raw_id_fields = ('agency', 'jurisdiction_profile')

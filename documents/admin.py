from django.contrib import admin

from .models import GeneratedDocument


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'doc_type', 'case_number', 'status',
        'narrative_style', 'created_at',
    )
    list_filter = ('doc_type', 'status', 'narrative_style')
    search_fields = ('case_number', 'user__email')
    raw_id_fields = ('user',)
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'model_used',
        'tokens_used', 'generation_time_ms',
    )

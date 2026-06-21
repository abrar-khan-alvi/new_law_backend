from django.contrib import admin

from .models import DocumentChunk, TrainingDocument


@admin.register(TrainingDocument)
class TrainingDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'is_indexed', 'chunk_count', 'uploaded_by', 'created_at')
    list_filter = ('doc_type', 'is_indexed')
    search_fields = ('title', 'original_filename')
    readonly_fields = ('chunk_count', 'is_indexed', 'created_at', 'updated_at')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('training_doc', 'doc_type', 'chunk_index')
    list_filter = ('doc_type',)
    search_fields = ('text',)

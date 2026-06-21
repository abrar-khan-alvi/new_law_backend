from rest_framework import serializers

from .models import TrainingDocument


class TrainingDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.CharField(
        source='uploaded_by.email', default=None, read_only=True)

    class Meta:
        model = TrainingDocument
        fields = [
            'id', 'doc_type', 'title', 'original_filename',
            'is_indexed', 'chunk_count', 'uploaded_by_email', 'created_at',
        ]
        read_only_fields = fields

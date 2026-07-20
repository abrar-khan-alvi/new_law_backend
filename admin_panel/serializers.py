from rest_framework import serializers

from accounts.models import User
from documents.models import GeneratedDocument
from documents.serializers import GeneratedDocumentSerializer

from .models import AuditLog


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    plan = serializers.CharField(source='subscription.plan.name', default=None, read_only=True)
    agency_name = serializers.CharField(source='agency.name', default=None, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'badge_number', 'department_name',
            'is_active', 'email_verified', 'is_supervisor', 'plan',
            'agency', 'agency_name',
            'last_active', 'created_at',
        ]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Admin-editable fields for managing accounts."""
    class Meta:
        model = User
        fields = ['role', 'is_active', 'is_supervisor', 'agency']


class AdminDocumentSerializer(serializers.ModelSerializer):
    """Compact row for the admin's cross-user document list."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    agency_name = serializers.CharField(source='user.agency.name', default=None, read_only=True)
    leak_flag_count = serializers.SerializerMethodField()
    quality_flag_count = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedDocument
        fields = [
            'id', 'user_email', 'agency_name', 'doc_type', 'case_number', 'status',
            'review_status', 'narrative_style', 'model_used', 'generation_time_ms',
            'leak_flag_count', 'quality_flag_count', 'created_at',
        ]

    def get_leak_flag_count(self, obj):
        return len(obj.leak_flags or [])

    def get_quality_flag_count(self, obj):
        return len(obj.quality_flags or [])


class AdminGeneratedDocumentSerializer(GeneratedDocumentSerializer):
    """
    Full document detail plus officer/agency identity. The officer-facing
    GeneratedDocumentSerializer omits those fields since an officer always
    already knows it's their own document — but an admin viewing someone
    else's document (e.g. from the review queue) needs to know whose it is.
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    agency_name = serializers.CharField(source='user.agency.name', default=None, read_only=True)

    class Meta(GeneratedDocumentSerializer.Meta):
        fields = GeneratedDocumentSerializer.Meta.fields + ['user_email', 'agency_name']
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'actor_label', 'action', 'severity', 'detail', 'created_at']

from rest_framework import serializers

from accounts.models import User
from documents.models import GeneratedDocument


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    plan = serializers.CharField(source='subscription.plan.name', default=None, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'department_name',
            'is_active', 'is_verified', 'email_verified', 'plan',
            'last_active', 'created_at',
        ]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Admin-editable fields for managing accounts."""
    class Meta:
        model = User
        fields = ['role', 'is_active', 'is_verified']


class AdminDocumentSerializer(serializers.ModelSerializer):
    """Compact row for the admin's cross-user document list."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    leak_flag_count = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedDocument
        fields = [
            'id', 'user_email', 'doc_type', 'case_number', 'status',
            'narrative_style', 'model_used', 'generation_time_ms',
            'leak_flag_count', 'created_at',
        ]

    def get_leak_flag_count(self, obj):
        return len(obj.leak_flags or [])

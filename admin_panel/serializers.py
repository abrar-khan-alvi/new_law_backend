from rest_framework import serializers

from accounts.models import User


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

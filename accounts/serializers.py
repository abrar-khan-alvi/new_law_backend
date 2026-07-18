from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Agency, JurisdictionProfile


class JurisdictionProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JurisdictionProfile
        fields = [
            'id', 'name', 'jurisdiction_type', 'state', 'county',
            'default_legal_citations',
        ]


class AgencySerializer(serializers.ModelSerializer):
    jurisdiction_profile_name = serializers.CharField(
        source='jurisdiction_profile.name', read_only=True, default=None,
    )
    seal_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Agency
        fields = [
            'id', 'name', 'jurisdiction_type', 'jurisdiction_profile', 'jurisdiction_profile_name',
            'state', 'county', 'city',
            'court_name', 'judicial_district', 'division', 'court_caption',
            'judge_title', 'prosecuting_authority', 'case_number_format',
            'ori', 'default_legal_citations', 'seal_image_url',
            'requires_supervisor_review', 'requires_prosecutor_review',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_seal_image_url(self, obj):
        if not obj.seal_image_key:
            return None
        from utils.storage import media_url
        return media_url(obj.seal_image_key)


# ── Profile ──────────────────────────────────────────────────────────
class SubscriptionBriefSerializer(serializers.Serializer):
    plan = serializers.CharField(source='plan.name')
    plan_display = serializers.CharField(source='plan.display_name')
    status = serializers.CharField()
    documents_generated_this_month = serializers.IntegerField()
    warrants_generated_this_month = serializers.IntegerField()
    # null = unlimited for both limits below.
    document_limit = serializers.IntegerField(source='plan.document_limit', allow_null=True)
    warrant_document_limit = serializers.IntegerField(source='plan.warrant_document_limit', allow_null=True)
    current_period_end = serializers.DateTimeField()


class UserProfileSerializer(serializers.ModelSerializer):
    subscription = SubscriptionBriefSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    agency = AgencySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name',
            'role', 'agency', 'badge_number', 'department_name', 'department_address',
            'department_state', 'ori', 'phone_number', 'rank', 'division',
            'email_verified', 'is_supervisor', 'subscription',
            'last_active', 'created_at',
        ]
        read_only_fields = [
            'id', 'email', 'role', 'email_verified', 'is_supervisor', 'created_at',
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'badge_number',
            'department_name', 'department_address', 'department_state',
            'ori', 'phone_number', 'rank', 'division',
        ]


# ── Registration ─────────────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 'first_name', 'last_name',
            'badge_number', 'department_name', 'department_address',
            'department_state', 'ori', 'phone_number', 'rank', 'division',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(role=User.Role.OFFICER, **validated_data)
        user.set_password(password)
        user.save()  # post_save signal creates the free subscription
        return user


# ── Login (JWT) ──────────────────────────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.role != 'admin' and not self.user.email_verified:
            raise serializers.ValidationError(
                'Email not verified. Please check your inbox for the verification link.'
            )

        from django.utils import timezone
        self.user.last_active = timezone.now()
        self.user.save(update_fields=['last_active'])
        data['user'] = UserProfileSerializer(self.user).data
        return data


# ── Email verification ───────────────────────────────────────────────
class EmailField(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()


# ── Password reset ───────────────────────────────────────────────────
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

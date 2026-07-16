from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import send_password_reset_email, send_verification_email
from .models import EmailOTP, User
from .otp import seconds_until_resend, verify_otp
from .permissions import IsAdmin
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    VerifyEmailSerializer,
    AgencySerializer,
)


class RegisterView(APIView):
    """POST /api/auth/register/ — create account + send verification email."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email(user)
        return Response(
            {'message': 'Account created. Check your email to verify your address.',
             'user': UserProfileSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """POST /api/auth/verify-email/ — confirm email with uid + token."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data['email']).first()
        if user is None:
            return Response({'error': 'Invalid code.'}, status=400)
        if user.email_verified:
            return Response({'message': 'Email already verified.'})

        ok, message = verify_otp(
            user, EmailOTP.Purpose.EMAIL_VERIFICATION, serializer.validated_data['code'])
        if not ok:
            return Response({'error': message}, status=400)

        user.email_verified = True
        user.save(update_fields=['email_verified'])
        return Response({'message': 'Email verified. You can now log in.'})


class ResendVerificationView(APIView):
    """POST /api/auth/resend-verification/ — re-send the verification email."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email', '')
        user = User.objects.filter(email=email).first()
        # Always return the same response (don't leak which emails exist), and
        # respect the resend cooldown to prevent code spamming.
        if user and not user.email_verified and not seconds_until_resend(
            user, EmailOTP.Purpose.EMAIL_VERIFICATION
        ):
            send_verification_email(user)
        return Response({'message': 'If the account exists and is unverified, an email was sent.'})


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — email + password → JWT access/refresh + profile."""
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data['refresh']).blacklist()
        except KeyError:
            return Response({'error': 'refresh token is required.'}, status=400)
        except Exception:
            return Response({'error': 'Invalid refresh token.'}, status=400)
        return Response({'message': 'Logged out.'}, status=205)


class ProfileView(APIView):
    """GET / PATCH /api/auth/profile/ — current user's profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)


class AgencyCreateView(APIView):
    """POST /api/auth/agencies/ — create an agency and link it to the current officer."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.agency:
            return Response({'error': 'You are already assigned to an agency.'}, status=400)
            
        serializer = AgencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agency = serializer.save()
        
        request.user.agency = agency
        request.user.save(update_fields=['agency'])
        
        return Response(AgencySerializer(agency).data, status=status.HTTP_201_CREATED)


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/ — change while logged in."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Current password is incorrect.'}, status=400)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response({'message': 'Password changed.'})


class PasswordResetRequestView(APIView):
    """POST /api/auth/password-reset/ — email a reset link."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data['email']).first()
        if user:
            send_password_reset_email(user)
        return Response({'message': 'If the account exists, a reset email was sent.'})


class PasswordResetConfirmView(APIView):
    """POST /api/auth/password-reset/confirm/ — set new password via token."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data['email']).first()
        if user is None:
            return Response({'error': 'Invalid code.'}, status=400)

        ok, message = verify_otp(
            user, EmailOTP.Purpose.PASSWORD_RESET, serializer.validated_data['code'])
        if not ok:
            return Response({'error': message}, status=400)

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'message': 'Password has been reset. You can now log in.'})


# ── Admin endpoints ──────────────────────────────────────────────────
class VerifyOfficerView(APIView):
    """POST /api/auth/verify-officer/<pk>/ — admin vets an officer account."""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role='officer')
        except User.DoesNotExist:
            return Response({'error': 'Officer not found.'}, status=404)
        user.is_verified = True
        user.verified_at = timezone.now()
        user.verified_by = request.user
        user.save(update_fields=['is_verified', 'verified_at', 'verified_by'])
        return Response({'message': f'{user.email} has been verified.'})


class UserListView(APIView):
    """GET /api/auth/users/ — admin: list all users with subscription info."""
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.select_related('subscription__plan').all()
        return Response(UserProfileSerializer(users, many=True).data)

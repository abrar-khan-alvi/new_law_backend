from axes.handlers.proxy import AxesProxyHandler
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import send_password_reset_email, send_verification_email
from .models import EmailOTP, User
from .otp import seconds_until_resend, verify_otp
from .permissions import IsAdmin
from utils.audit_log import log_event
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    VerifyEmailSerializer,
)


def _blacklist_all_tokens(user):
    """Revoke every outstanding refresh token for this user. Called on
    password change/reset so a token that leaked (plausibly the whole reason
    for the reset) doesn't keep working afterward."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


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

    def post(self, request, *args, **kwargs):
        email = (request.data.get('email') or '').strip() or '(none provided)'

        # django-axes' lockout normally surfaces through AxesMiddleware reading
        # a flag set on the request object passed into authenticate() — but
        # simplejwt passes the DRF-wrapped Request (via serializer context),
        # a different object than the raw HttpRequest the middleware sees, so
        # that flag never arrives. Checked explicitly here instead so a locked
        # out account gets an honest 429, not a generic "wrong credentials".
        credentials = {settings.AXES_USERNAME_FORM_FIELD: email}
        if not AxesProxyHandler.is_allowed(request, credentials):
            log_event(None, 'auth.login_locked_out', severity='warning', email=email)
            return Response(
                {'error': {'detail': 'Too many failed login attempts. Try again later.',
                           'code': 'locked_out'}},
                status=429,
            )

        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            log_event(None, 'auth.login_failed', severity='warning', email=email)
            raise
        log_event(None, 'auth.login', severity='info', email=email)
        return response


class GoogleLoginView(APIView):
    """Exchange a Google Identity Services ID token for the app's JWT pair.

    New accounts are verified officers with no agency. Agency assignment stays
    exclusively in the admin workflow and is required later for export.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        credential = request.data.get('credential')
        client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        if not client_id:
            return Response({'error': {'detail': 'Google sign-in is not configured.', 'code': 'google_not_configured'}}, status=503)
        if not credential:
            return Response({'error': {'detail': 'Google credential is required.'}}, status=400)

        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token
            claims = id_token.verify_oauth2_token(
                credential, google_requests.Request(), client_id,
            )
        except (ValueError, TypeError):
            return Response({'error': {'detail': 'Google could not verify this sign-in.', 'code': 'invalid_google_token'}}, status=400)

        email = (claims.get('email') or '').strip().lower()
        if not email or not claims.get('email_verified'):
            return Response({'error': {'detail': 'A verified Google email is required.'}}, status=400)

        user = User.objects.filter(email__iexact=email).first()
        created = user is None
        if created:
            user = User(
                email=email, role=User.Role.OFFICER, email_verified=True,
                first_name=(claims.get('given_name') or '')[:150],
                last_name=(claims.get('family_name') or '')[:150],
            )
            user.set_unusable_password()
            user.save()
        elif user.role == User.Role.ADMIN:
            return Response({'error': {'detail': 'Administrators must use the Admin Portal.', 'code': 'admin_google_login_blocked'}}, status=403)
        elif not user.email_verified:
            user.email_verified = True
            user.save(update_fields=['email_verified'])

        user.last_active = timezone.now()
        user.save(update_fields=['last_active'])
        refresh = RefreshToken.for_user(user)
        log_event(user, 'auth.google_login', severity='info', account_created=created)
        return Response({
            'access': str(refresh.access_token), 'refresh': str(refresh),
            'user': UserProfileSerializer(user).data, 'created': created,
        })


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
        log_event(request.user, 'auth.logout', severity='info')
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
        _blacklist_all_tokens(request.user)
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
        _blacklist_all_tokens(user)
        return Response({'message': 'Password has been reset. You can now log in.'})


# ── Admin endpoints ──────────────────────────────────────────────────
class UserListView(APIView):
    """GET /api/auth/users/ — admin: list all users with subscription info."""
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.select_related('subscription__plan').all()
        return Response(UserProfileSerializer(users, many=True).data)

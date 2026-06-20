import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_verification_token

logger = logging.getLogger(__name__)


def _uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def send_verification_email(user):
    """Email a verification link pointing at the frontend."""
    uid = _uid(user)
    token = email_verification_token.make_token(user)
    link = f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"

    send_mail(
        subject='Verify your email address',
        message=(
            f"Hello,\n\n"
            f"Please confirm your email address to activate your account:\n\n"
            f"{link}\n\n"
            f"If you did not create an account, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info("Verification email sent to %s", user.email)


def send_password_reset_email(user):
    """Email a password-reset link pointing at the frontend."""
    uid = _uid(user)
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    send_mail(
        subject='Reset your password',
        message=(
            f"Hello,\n\n"
            f"We received a request to reset your password. Use the link below:\n\n"
            f"{link}\n\n"
            f"If you did not request this, you can safely ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info("Password reset email sent to %s", user.email)

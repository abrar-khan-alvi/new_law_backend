"""
Numeric OTP service for email verification and password reset.

Codes are random N-digit numbers (default 6). Only an HMAC-SHA256 hash (keyed by
SECRET_KEY) is stored — never the plaintext. Codes expire (default 10 min), allow
a limited number of attempts (default 5), and resends are rate-limited (default 60s).
"""
import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import EmailOTP


def _ttl_minutes():
    return getattr(settings, 'OTP_TTL_MINUTES', 10)


def _max_attempts():
    return getattr(settings, 'OTP_MAX_ATTEMPTS', 5)


def _cooldown_seconds():
    return getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)


def _hash(code: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), code.encode(), hashlib.sha256
    ).hexdigest()


def generate_otp(user, purpose) -> str:
    """Create a fresh code (invalidating prior active ones) and return the plaintext."""
    length = getattr(settings, 'OTP_LENGTH', 6)
    code = ''.join(str(secrets.randbelow(10)) for _ in range(length))

    # Invalidate any still-active codes for this user+purpose.
    EmailOTP.objects.filter(user=user, purpose=purpose, used=False).update(used=True)
    EmailOTP.objects.create(
        user=user,
        purpose=purpose,
        code_hash=_hash(code),
        expires_at=timezone.now() + timedelta(minutes=_ttl_minutes()),
    )
    return code


def seconds_until_resend(user, purpose) -> int:
    """0 if a resend is allowed now, else seconds the caller must wait."""
    latest = (EmailOTP.objects
              .filter(user=user, purpose=purpose)
              .order_by('-created_at').first())
    if not latest:
        return 0
    elapsed = (timezone.now() - latest.created_at).total_seconds()
    remaining = _cooldown_seconds() - elapsed
    return max(0, int(remaining))


def verify_otp(user, purpose, code) -> tuple[bool, str]:
    """Validate a submitted code. Returns (ok, message)."""
    otp = (EmailOTP.objects
           .filter(user=user, purpose=purpose, used=False)
           .order_by('-created_at').first())
    if not otp:
        return False, 'No active code. Please request a new one.'
    if otp.is_expired():
        return False, 'Code expired. Please request a new one.'
    if otp.attempts >= _max_attempts():
        otp.used = True
        otp.save(update_fields=['used'])
        return False, 'Too many attempts. Please request a new code.'
    if not hmac.compare_digest(otp.code_hash, _hash(str(code))):
        otp.attempts += 1
        otp.save(update_fields=['attempts'])
        return False, 'Invalid code.'

    otp.used = True
    otp.save(update_fields=['used'])
    return True, 'OK'

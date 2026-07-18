"""Production settings — HTTPS, security hardening, real services."""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import SECRET_KEY

DEBUG = False

# Fail fast rather than silently signing sessions/JWTs — and the OTP HMAC
# (accounts/otp.py) — with a publicly-known key because DJANGO_SECRET_KEY was
# never set for this deploy.
if not SECRET_KEY or SECRET_KEY == 'dev-insecure-change-me':
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY must be set to a real, unique secret in production — '
        'refusing to start with the insecure development default.'
    )

# ── HTTPS / security ─────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files served via WhiteNoise behind the WSGI server.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MIDDLEWARE.insert(  # noqa: F405
    1, 'whitenoise.middleware.WhiteNoiseMiddleware'
)

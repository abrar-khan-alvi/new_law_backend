"""
Base settings shared across all environments.
Environment-specific overrides live in development.py / production.py.
"""
from pathlib import Path

import environ

# ── Paths ────────────────────────────────────────────────────────────
# BASE_DIR = project root (where manage.py lives)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Environment ──────────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
    USE_SQLITE=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:3000']),
)
# Read .env at the project root if present.
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='dev-insecure-change-me')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# ── Applications ─────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    # Added in later phases as modules are built:
    # 'storages', 'axes', 'drf_spectacular',
]

LOCAL_APPS = [
    'accounts',
    'subscriptions',
    'ai_engine',
    'documents',
    'blog',
    'payments',
    'admin_panel',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom user model (must be set before the first migration runs).
AUTH_USER_MODEL = 'accounts.User'

# ── Middleware ───────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# ── Database ─────────────────────────────────────────────────────────
# Step 1: default to SQLite so the scaffold runs with zero infra.
# Step 2: set USE_SQLITE=False in .env to switch to PostgreSQL (+pgvector).
if env('USE_SQLITE'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='law_enforcement_db'),
            'USER': env('DB_USER', default='le_user'),
            'PASSWORD': env('DB_PASSWORD', default=''),
            'HOST': env('DB_HOST', default='localhost'),
            'PORT': env('DB_PORT', default='5432'),
        }
    }

# ── Password validation ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalization ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static & media ───────────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CORS ─────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')

# ── Django REST Framework ────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# File upload size limit — 500MB (large video uploads in the blog module)
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000

# ── Email (SMTP) ─────────────────────────────────────────────────────
# Used for email verification + password reset (Step 5).
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', default=15)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# ── JWT (djangorestframework-simplejwt) ──────────────────────────────
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── AI model ─────────────────────────────────────────────────────────
# AI_MODE: 'mock' (default, no infra) | 'ollama' (local dev) | 'bedrock' (prod)
AI_MODE = env('AI_MODE', default='mock')
USE_LOCAL_MODEL = env.bool('USE_LOCAL_MODEL', default=True)
LOCAL_MODEL_URL = env('LOCAL_MODEL_URL', default='http://localhost:11434')
LOCAL_MODEL_NAME = env('LOCAL_MODEL_NAME', default='llama3.1:8b')
BEDROCK_MODEL_ID = env('BEDROCK_MODEL_ID', default='')
BEDROCK_REGION = env('BEDROCK_REGION', default='us-east-1')

# ── RAG / embeddings ─────────────────────────────────────────────────
EMBEDDING_MODEL = env('EMBEDDING_MODEL', default='all-MiniLM-L6-v2')
EMBEDDING_DIM = env.int('EMBEDDING_DIM', default=384)   # matches all-MiniLM-L6-v2
RAG_TOP_K = env.int('RAG_TOP_K', default=3)
RAG_CHUNK_SIZE = env.int('RAG_CHUNK_SIZE', default=1000)      # characters
RAG_CHUNK_OVERLAP = env.int('RAG_CHUNK_OVERLAP', default=150)

# ── AWS / S3 ─────────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_REGION = env('AWS_REGION', default='us-east-1')
AWS_S3_BUCKET = env('AWS_S3_BUCKET', default='')
AWS_S3_BUCKET_REGION = env('AWS_S3_BUCKET_REGION', default=AWS_REGION)

# ── Stripe (payments) ────────────────────────────────────────────────
# Code is present but DORMANT until a secret key is configured.
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_PRICES = {
    ('basic', 'monthly'): env('STRIPE_PRICE_BASIC_MONTHLY', default=''),
    ('basic', 'yearly'): env('STRIPE_PRICE_BASIC_YEARLY', default=''),
    ('pro', 'monthly'): env('STRIPE_PRICE_PRO_MONTHLY', default=''),
    ('pro', 'yearly'): env('STRIPE_PRICE_PRO_YEARLY', default=''),
    ('enterprise', 'monthly'): env('STRIPE_PRICE_ENTERPRISE_MONTHLY', default=''),
    ('enterprise', 'yearly'): env('STRIPE_PRICE_ENTERPRISE_YEARLY', default=''),
}
# Live checkout/webhook only run when a key is present.
PAYMENTS_ENABLED = bool(STRIPE_SECRET_KEY)

# ── Logging (incl. audit) ────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'audit': {'format': '[AUDIT] %(asctime)s %(message)s'},
        'simple': {'format': '%(levelname)s %(name)s %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
        'audit': {'class': 'logging.StreamHandler', 'formatter': 'audit'},
    },
    'loggers': {
        'audit': {'handlers': ['audit'], 'level': 'INFO', 'propagate': False},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# ── Celery ───────────────────────────────────────────────────────────
from celery.schedules import crontab  # noqa: E402

CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'reset-monthly-usage': {
        'task': 'subscriptions.tasks.reset_monthly_usage',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
    'cleanup-failed-documents': {
        'task': 'documents.tasks.cleanup_failed_documents',
        'schedule': crontab(hour=2, minute=0),  # daily at 02:00
    },
}

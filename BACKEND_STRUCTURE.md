# Law Enforcement Workflow Automation System
## Complete Backend Structure Reference

**Project:** Law Enforcement Workflow Automation System
**Stack:** Python 3.11 · Django 5 · PostgreSQL (pgvector) · Redis · AWS · Llama 3.1 8B
**Prepared by:** Towhidul Islam — Web Chrome
**Date:** June 2026

---

## Build & Run Conventions (confirmed 2026-06-20)

These are standing constraints for building this backend:

1. **Docker only.** The backend is built and run exclusively through Docker — never run `python` / `pip` / `manage.py` on the host. Use:
   - `docker compose up --build` — start the stack
   - `docker compose exec backend python manage.py <cmd>` — migrations, shell, createsuperuser
   - `docker compose run --rm backend <cmd>` — one-off commands
2. **PostgreSQL only.** Single datastore is PostgreSQL (`pgvector/pgvector:pg16` via the `db` compose service). MongoDB / `djongo` is **dropped** (unmaintained on Django 5). Assume Postgres semantics when writing models/migrations.
3. **Compose uses Postgres directly** — `USE_SQLITE=False`; the `backend` container connects to the `db` service. SQLite remains only as an optional infra-free fallback in settings, not used in practice.
4. **Auth = self-hosted Django + JWT** (NOT Firebase). Django owns users/passwords; login returns a JWT via `djangorestframework-simplejwt`. **Email is the login field** (`USERNAME_FIELD = 'email'`, no `username`). Gmail SMTP sends email-verification and password-reset emails. No third-party identity provider — chosen for confidentiality of LE user data. `firebase-admin` is dropped from the stack. (Supersedes the Firebase design described in §3 Authentication below.)

---

## Table of Contents

1. [Full Project Folder Structure](#1-full-project-folder-structure)
2. [requirements.txt — Complete](#2-requirementstxt--complete)
3. [Authentication](#3-authentication)
4. [Blog Module](#4-blog-module)
5. [Document Generation Features](#5-document-generation-features)
6. [Subscriptions & Payments](#6-subscriptions--payments)
7. [Admin Panel](#7-admin-panel)
8. [AI Engine](#8-ai-engine)
9. [URL Configuration](#9-url-configuration)
10. [Settings Structure](#10-settings-structure)
11. [Database Models Summary](#11-database-models-summary)
12. [Environment Variables (.env)](#12-environment-variables-env)
13. [Celery & Background Tasks](#13-celery--background-tasks)
14. [Storage (S3)](#14-storage-s3)
15. [Docker & Deployment Files](#15-docker--deployment-files)

---

## 1. Full Project Folder Structure

```
law_enforcement_backend/
│
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── pytest.ini
├── setup.cfg
│
├── core/                                   # Django project config
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── celery.py                           # Celery app config
│   ├── urls.py                             # Root URL config
│   └── settings/
│       ├── __init__.py
│       ├── base.py                         # Shared settings
│       ├── development.py                  # Dev overrides
│       └── production.py                   # Prod overrides (HTTPS, logging)
│
├── accounts/                               # Auth & user profiles
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                           # User, UserProfile
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py                      # IsOfficer, IsAdmin, HasQuota
│   ├── authentication.py                   # Firebase token verifier
│   ├── signals.py                          # Auto-create subscription on register
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_views.py
│       └── test_auth.py
│
├── blog/                                   # Blog posts + media uploads
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                           # BlogPost, BlogMedia, Video, Tag
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── filters.py                          # Filter by tag, category, date
│   ├── pagination.py
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       └── test_views.py
│
├── documents/                              # AI document generation
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                           # GeneratedDocument, DocumentVersion
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py                            # Celery: async generation
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── pdf.py                          # ReportLab PDF (Smyrna PD format)
│   │   └── word.py                         # python-docx Word export
│   └── tests/
│       ├── __init__.py
│       ├── test_generation.py
│       └── test_export.py
│
├── ai_engine/                              # All AI / ML logic
│   ├── __init__.py
│   ├── apps.py
│   ├── model_client.py                     # Ollama (dev) / Bedrock (prod)
│   ├── prompt_builder.py                   # Prompt templates per doc type
│   ├── rag_pipeline.py                     # Vector search + context injection
│   ├── document_parser.py                  # PDF/DOCX text extractor
│   ├── embeddings.py                       # AWS Titan Embeddings
│   ├── models.py                           # TrainingDocument, DocumentChunk
│   ├── serializers.py
│   ├── views.py                            # Training doc upload endpoint
│   ├── urls.py
│   ├── tasks.py                            # Celery: async embedding indexing
│   └── fine_tuning/
│       ├── __init__.py
│       ├── prepare_dataset.py              # Build JSONL from training docs
│       └── run_finetune.py                 # LoRA fine-tune script
│
├── subscriptions/                          # Plans, limits, access control
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                           # Subscription, Plan, UsageLog
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py                      # HasActiveSubscription, HasQuota
│   └── tests/
│       ├── __init__.py
│       └── test_subscriptions.py
│
├── payments/                               # Stripe integration
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                           # Payment, Invoice
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── webhooks.py                         # Stripe event handlers
│   └── tests/
│       ├── __init__.py
│       └── test_payments.py
│
├── admin_panel/                            # Platform admin APIs
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py
│   ├── urls.py
│   └── serializers.py
│
└── utils/                                  # Shared utilities
    ├── __init__.py
    ├── s3.py                               # S3 upload/download/signed URLs
    ├── validators.py                       # File type, size validators
    ├── pagination.py                       # Standard pagination class
    ├── audit_log.py                        # CJIS-compliant audit logging
    ├── exceptions.py                       # Custom API exceptions
    └── media_processor.py                  # Image resize, video thumbnail
```

---

## 2. requirements.txt — Complete

```txt
# ════════════════════════════════════════
# CORE DJANGO
# ════════════════════════════════════════
Django==5.0.6
djangorestframework==3.15.2
django-cors-headers==4.4.0
django-environ==0.11.2
django-filter==24.3
django-extensions==3.2.3
djangorestframework-simplejwt==5.3.1

# ════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════
psycopg2-binary==2.9.9           # PostgreSQL adapter
pgvector==0.3.2                  # Vector embeddings in PostgreSQL
pymongo==4.8.0                   # MongoDB driver
djongo==1.3.6                    # Django + MongoDB ORM bridge
redis==5.0.7                     # Redis client

# ════════════════════════════════════════
# AUTHENTICATION
# ════════════════════════════════════════
firebase-admin==6.5.0            # Firebase token verification
PyJWT==2.9.0                     # JWT handling
cryptography==43.0.0             # JWT signing/verification
django-axes==6.5.0               # Brute force login protection

# ════════════════════════════════════════
# AWS
# ════════════════════════════════════════
boto3==1.35.0                    # AWS SDK (Bedrock, S3, SES)
botocore==1.35.0
django-storages==1.14.4          # S3 file storage backend
watchtower==3.3.1                # CloudWatch logging handler

# ════════════════════════════════════════
# AI / ML — MODEL INFERENCE
# ════════════════════════════════════════
requests==2.32.3                 # Ollama HTTP calls (local model)
langchain==0.2.14                # LLM orchestration framework
langchain-community==0.2.12      # Community integrations
langchain-aws==0.1.18            # AWS Bedrock via LangChain

# ════════════════════════════════════════
# AI / ML — EMBEDDINGS & RAG
# ════════════════════════════════════════
sentence-transformers==3.1.0     # Local embedding fallback
numpy==1.26.4                    # Array operations

# ════════════════════════════════════════
# AI / ML — FINE-TUNING (run separately on GPU machine)
# ════════════════════════════════════════
# Uncomment only on the fine-tuning machine:
# torch==2.4.0
# transformers==4.44.2
# peft==0.12.0
# trl==0.9.6
# datasets==2.21.0
# accelerate==0.33.0
# bitsandbytes==0.43.3           # QLoRA 4-bit quantization

# ════════════════════════════════════════
# DOCUMENT PARSING (training doc ingestion)
# ════════════════════════════════════════
PyMuPDF==1.24.9                  # PDF text extraction (fitz)
python-docx==1.1.2               # DOCX text extraction + Word export
pdfplumber==0.11.3               # Alternative PDF parser (tables)
mammoth==1.8.0                   # DOCX to clean text/HTML

# ════════════════════════════════════════
# DOCUMENT GENERATION (PDF export)
# ════════════════════════════════════════
reportlab==4.2.2                 # PDF generation (Smyrna PD format)
WeasyPrint==62.3                 # HTML-to-PDF alternative
Pillow==10.4.0                   # Image processing for PDF

# ════════════════════════════════════════
# BLOG — MEDIA HANDLING
# ════════════════════════════════════════
Pillow==10.4.0                   # Image resize, thumbnail, format conversion
python-magic==0.4.27             # File type detection (MIME)
moviepy==1.0.3                   # Video thumbnail extraction
ffmpeg-python==0.2.0             # Video processing wrapper

# ════════════════════════════════════════
# PAYMENTS
# ════════════════════════════════════════
stripe==10.7.0                   # Stripe payments + webhooks

# ════════════════════════════════════════
# ASYNC TASKS
# ════════════════════════════════════════
celery==5.4.0                    # Task queue
django-celery-beat==2.7.0        # Periodic tasks (cron-style)
django-celery-results==2.5.1     # Store task results in DB
flower==2.0.1                    # Celery monitoring dashboard

# ════════════════════════════════════════
# API UTILITIES
# ════════════════════════════════════════
django-ratelimit==4.1.0          # Per-endpoint rate limiting
drf-spectacular==0.27.2          # OpenAPI/Swagger docs auto-generation
django-silk==5.1.0               # API profiling (dev only)

# ════════════════════════════════════════
# SECURITY
# ════════════════════════════════════════
django-csp==3.8                  # Content Security Policy headers
django-permissions-policy==4.21.0 # Feature-Policy headers
bleach==6.1.0                    # HTML sanitization (blog content)

# ════════════════════════════════════════
# UTILITIES
# ════════════════════════════════════════
python-decouple==3.8             # .env variable loading
python-dateutil==2.9.0           # Date parsing
pytz==2024.1                     # Timezone handling
shortuuid==1.0.13                # Short unique IDs for case numbers
Markdown==3.6                    # Markdown to HTML (blog)
python-slugify==8.0.4            # Auto-generate URL slugs
celery-progress==0.4             # Real-time task progress

# ════════════════════════════════════════
# PRODUCTION SERVER
# ════════════════════════════════════════
gunicorn==22.0.0                 # WSGI server
uvicorn==0.30.6                  # ASGI server (WebSockets)
whitenoise==6.7.0                # Static file serving
```

### requirements-dev.txt

```txt
# Development-only dependencies
-r requirements.txt

# Testing
pytest==8.3.2
pytest-django==4.8.0
pytest-cov==5.0.0
factory-boy==3.3.1               # Test data factories
faker==26.0.0                    # Fake data generation
responses==0.25.3                # Mock HTTP requests (Stripe, Firebase)
moto==5.0.12                     # Mock AWS services (S3, Bedrock)
freezegun==1.5.1                 # Freeze time in tests

# Code quality
black==24.8.0                    # Code formatter
flake8==7.1.0                    # Linter
isort==5.13.2                    # Import sorter
mypy==1.11.0                     # Type checking
django-stubs==5.0.4              # Django type stubs

# Debugging
django-debug-toolbar==4.4.2      # SQL query inspector
ipython==8.26.0                  # Better Django shell
django-silk==5.1.0               # Request profiling
```

---

## 3. Authentication

### Models (`accounts/models.py`)

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for law enforcement officers and admins.
    Authentication handled by Firebase — password field is unused.
    """

    class Role(models.TextChoices):
        FREE    = 'free',    'Free User'
        OFFICER = 'officer', 'Law Enforcement Officer'
        ADMIN   = 'admin',   'Platform Admin'

    # Firebase
    firebase_uid      = models.CharField(max_length=128, unique=True,
                                          blank=True, null=True, db_index=True)

    # Role
    role              = models.CharField(max_length=20, choices=Role.choices,
                                          default=Role.FREE)

    # Officer details
    badge_number      = models.CharField(max_length=50,  blank=True)
    department_name   = models.CharField(max_length=200, blank=True)
    department_address= models.TextField(blank=True)
    department_state  = models.CharField(max_length=50,  blank=True)
    ori               = models.CharField(max_length=20,  blank=True)
    phone_number      = models.CharField(max_length=20,  blank=True)
    rank              = models.CharField(max_length=100, blank=True)
    division          = models.CharField(max_length=100, blank=True)

    # Timestamps
    last_active       = models.DateTimeField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes  = [
            models.Index(fields=['firebase_uid']),
            models.Index(fields=['role']),
            models.Index(fields=['department_name']),
        ]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def has_active_subscription(self):
        sub = getattr(self, 'subscription', None)
        return sub and sub.status == 'active'

    @property
    def can_generate_document(self):
        sub = getattr(self, 'subscription', None)
        if not sub:
            return False
        return sub.documents_generated_this_month < sub.plan.document_limit
```

### Firebase Authentication (`accounts/authentication.py`)

```python
import firebase_admin
from firebase_admin import auth, credentials
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.utils import timezone
from .models import User
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase once at startup
_cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(_cred)


class FirebaseAuthentication(BaseAuthentication):
    """
    Validates Firebase ID tokens sent in the Authorization header.

    Header format:
        Authorization: Bearer <firebase_id_token>

    Flow:
        1. Extract token from header
        2. Verify with Firebase Admin SDK
        3. Get or create Django User from firebase_uid
        4. Auto-create Subscription on first login
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None     # Not a Firebase request — try next authenticator

        id_token = auth_header.split('Bearer ', 1)[1].strip()

        try:
            decoded_token = auth.verify_id_token(id_token)
        except auth.ExpiredIdTokenError:
            raise AuthenticationFailed('Firebase token has expired. Please log in again.')
        except auth.InvalidIdTokenError:
            raise AuthenticationFailed('Firebase token is invalid.')
        except Exception as e:
            logger.error(f"Firebase auth error: {e}")
            raise AuthenticationFailed('Authentication failed.')

        firebase_uid = decoded_token['uid']
        email        = decoded_token.get('email', '')
        name         = decoded_token.get('name', '')

        user, created = User.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={
                'username'   : email or firebase_uid,
                'email'      : email,
                'first_name' : name.split()[0] if name else '',
                'last_name'  : ' '.join(name.split()[1:]) if name else '',
            }
        )

        if created:
            self._setup_new_user(user)

        # Update last active
        user.last_active = timezone.now()
        user.save(update_fields=['last_active'])

        return (user, None)

    def _setup_new_user(self, user):
        """Auto-create free subscription for new users."""
        from subscriptions.models import Subscription, Plan
        free_plan = Plan.objects.filter(name='free').first()
        if free_plan:
            Subscription.objects.create(
                user   = user,
                plan   = free_plan,
                status = 'active',
            )
        logger.info(f"New user registered: {user.email}")
```

### Permissions (`accounts/permissions.py`)

```python
from rest_framework.permissions import BasePermission


class IsOfficer(BasePermission):
    """Verified law enforcement officers and admins only."""
    message = 'Access restricted to verified law enforcement officers.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [
                'officer', 'admin'
            ]
        )


class IsAdmin(BasePermission):
    """Platform admins only."""
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class HasActiveSubscription(BasePermission):
    """User must have an active paid subscription."""
    message = 'An active subscription is required to access this feature.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        sub = getattr(request.user, 'subscription', None)
        return sub and sub.status == 'active' and sub.plan.name != 'free'


class HasDocumentQuota(BasePermission):
    """User has not exceeded their monthly document limit."""
    message = 'Monthly document generation limit reached. Please upgrade your plan.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.can_generate_document


class IsOwnerOrAdmin(BasePermission):
    """Object-level: only the owner or an admin can access."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user == request.user
```

### Auth Views (`accounts/views.py`)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import User
from .serializers import (
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
)


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Called after Firebase registration to save officer profile details.
    Firebase token in header creates the User record automatically.
    This endpoint fills in the officer-specific fields.
    """
    permission_classes = [AllowAny]  # FirebaseAuthentication still runs

    def post(self, request):
        serializer = UserRegistrationSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            user      = serializer.save()
            user.role = 'officer'
            user.save()
            return Response(
                UserProfileSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=400)


class ProfileView(APIView):
    """
    GET  /api/auth/profile/   → Return current user profile
    PATCH /api/auth/profile/  → Update profile fields
    """

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UserListView(APIView):
    """
    GET /api/auth/users/
    Admin: list all users with subscription info.
    """
    from accounts.permissions import IsAdmin
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.select_related('subscription__plan').all()
        return Response(UserProfileSerializer(users, many=True).data)
```

### Auth Serializers (`accounts/serializers.py`)

```python
from rest_framework import serializers
from .models import User


class SubscriptionBriefSerializer(serializers.Serializer):
    plan                      = serializers.CharField(source='plan.name')
    status                    = serializers.CharField()
    documents_generated_this_month = serializers.IntegerField()
    document_limit            = serializers.IntegerField(source='plan.document_limit')
    current_period_end        = serializers.DateTimeField()


class UserProfileSerializer(serializers.ModelSerializer):
    subscription = SubscriptionBriefSerializer(read_only=True)
    full_name    = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name',
            'role', 'badge_number', 'department_name', 'department_address',
            'department_state', 'ori', 'phone_number', 'rank', 'division',
            'is_supervisor', 'subscription', 'last_active', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_supervisor', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'first_name', 'last_name', 'badge_number',
            'department_name', 'department_address',
            'department_state', 'ori', 'phone_number', 'rank', 'division',
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'first_name', 'last_name', 'badge_number',
            'department_name', 'department_address',
            'phone_number', 'rank', 'division',
        ]
```

---

## 4. Blog Module

Supports all combinations:
- Text only
- Text + Image
- Text + Video
- Text + Image + Video
- Image only
- Video only

### Models (`blog/models.py`)

```python
from django.db import models
from accounts.models import User
from django.utils.text import slugify
import uuid


class Tag(models.Model):
    name       = models.CharField(max_length=50, unique=True)
    slug       = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_tags'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    """
    Flexible blog post supporting all media combinations:
    - Text only
    - Text + Image(s)
    - Text + Video(s)
    - Text + Image(s) + Video(s)
    - Image(s) only
    - Video(s) only

    Media is stored separately in BlogMedia model (one-to-many).
    """

    class PostType(models.TextChoices):
        TEXT            = 'text',             'Text Only'
        TEXT_IMAGE      = 'text_image',       'Text + Image'
        TEXT_VIDEO      = 'text_video',       'Text + Video'
        TEXT_IMAGE_VIDEO= 'text_image_video', 'Text + Image + Video'
        IMAGE           = 'image',            'Image Only'
        VIDEO           = 'video',            'Video Only'

    class Category(models.TextChoices):
        LAW_ENFORCEMENT = 'law_enforcement', 'Law Enforcement'
        TECHNOLOGY      = 'technology',      'Technology'
        AI              = 'ai',              'Artificial Intelligence'
        LEGAL_UPDATES   = 'legal_updates',   'Legal Updates'
        TRAINING        = 'training',        'Training & Education'
        POLICY          = 'policy',          'Policy & Procedure'
        GENERAL         = 'general',         'General'

    # Identity
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                    editable=False)
    title       = models.CharField(max_length=500, blank=True)
    slug        = models.SlugField(max_length=550, unique=True, blank=True)
    post_type   = models.CharField(max_length=30, choices=PostType.choices,
                                    default=PostType.TEXT)
    category    = models.CharField(max_length=30, choices=Category.choices,
                                    default=Category.GENERAL)

    # Content
    content     = models.TextField(blank=True)          # Main text body (Markdown)
    content_html= models.TextField(blank=True)          # Rendered HTML (auto-generated)
    excerpt     = models.TextField(blank=True, max_length=500)
    cover_image = models.CharField(max_length=500, blank=True) # S3 key of cover image

    # Relations
    author      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, related_name='blog_posts')
    tags        = models.ManyToManyField(Tag, blank=True, related_name='posts')

    # Status
    is_published   = models.BooleanField(default=False)
    is_featured    = models.BooleanField(default=False)
    published_at   = models.DateTimeField(null=True, blank=True)

    # SEO
    meta_title       = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    # Stats
    view_count  = models.PositiveIntegerField(default=0)
    like_count  = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_posts'
        ordering = ['-published_at', '-created_at']
        indexes  = [
            models.Index(fields=['is_published', 'published_at']),
            models.Index(fields=['category']),
            models.Index(fields=['post_type']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter   = 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter  += 1

        # Auto-detect post_type based on attached media
        if self.pk:
            has_images = self.media.filter(media_type='image').exists()
            has_videos = self.media.filter(
                media_type__in=['video', 'video_url']).exists()
            has_text   = bool(self.content.strip())

            if has_text and has_images and has_videos:
                self.post_type = self.PostType.TEXT_IMAGE_VIDEO
            elif has_text and has_images:
                self.post_type = self.PostType.TEXT_IMAGE
            elif has_text and has_videos:
                self.post_type = self.PostType.TEXT_VIDEO
            elif has_images and has_videos:
                self.post_type = self.PostType.TEXT_IMAGE_VIDEO
            elif has_images:
                self.post_type = self.PostType.IMAGE
            elif has_videos:
                self.post_type = self.PostType.VIDEO
            elif has_text:
                self.post_type = self.PostType.TEXT

        # Render Markdown to HTML
        if self.content:
            import markdown
            self.content_html = markdown.markdown(
                self.content,
                extensions=['fenced_code', 'tables', 'nl2br']
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Post {self.id}"


class BlogMedia(models.Model):
    """
    Individual media item attached to a blog post.
    Supports: images, uploaded videos, embedded video URLs (YouTube/Vimeo).
    """

    class MediaType(models.TextChoices):
        IMAGE     = 'image',     'Image'
        VIDEO     = 'video',     'Uploaded Video'
        VIDEO_URL = 'video_url', 'Embedded Video URL (YouTube/Vimeo)'
        DOCUMENT  = 'document',  'Document'

    post        = models.ForeignKey(BlogPost, on_delete=models.CASCADE,
                                     related_name='media')
    media_type  = models.CharField(max_length=20, choices=MediaType.choices)

    # For uploaded files (stored in S3)
    s3_key      = models.CharField(max_length=500, blank=True)
    file_name   = models.CharField(max_length=255, blank=True)
    file_size   = models.PositiveIntegerField(default=0)      # bytes
    mime_type   = models.CharField(max_length=100, blank=True)

    # For video embeds
    video_url   = models.URLField(blank=True)                 # YouTube/Vimeo URL
    embed_html  = models.TextField(blank=True)                # Embed iframe HTML

    # Image metadata
    width       = models.PositiveIntegerField(default=0)
    height      = models.PositiveIntegerField(default=0)
    alt_text    = models.CharField(max_length=300, blank=True)
    caption     = models.CharField(max_length=500, blank=True)

    # Video metadata
    duration_seconds = models.PositiveIntegerField(default=0)
    thumbnail_s3_key = models.CharField(max_length=500, blank=True)

    # Order in post
    order       = models.PositiveIntegerField(default=0)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_media'
        ordering = ['order', 'created_at']

    @property
    def s3_url(self):
        """Generate a presigned S3 URL for this media item."""
        if self.s3_key:
            from utils.s3 import generate_presigned_url
            return generate_presigned_url(self.s3_key)
        return None

    def __str__(self):
        return f"{self.media_type} for post {self.post_id}"
```

### Blog Views (`blog/views.py`)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from accounts.permissions import IsAdmin
from .models import BlogPost, BlogMedia, Tag
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostCreateSerializer,
    BlogMediaSerializer,
    TagSerializer,
)
from .filters import BlogPostFilter
from utils.s3 import upload_file_to_s3, generate_presigned_url
from utils.media_processor import process_image, extract_video_thumbnail
import magic
import uuid


class BlogPostListView(APIView):
    """
    GET  /api/blog/posts/  → Public list (published only)
    POST /api/blog/posts/  → Admin create
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [AllowAny()]

    def get(self, request):
        posts = BlogPost.objects.filter(
            is_published=True
        ).select_related('author').prefetch_related('tags', 'media')

        # Filtering
        f = BlogPostFilter(request.GET, queryset=posts)

        # Pagination
        from utils.pagination import StandardPagination
        paginator = StandardPagination()
        page      = paginator.paginate_queryset(f.qs, request)
        serializer= BlogPostListSerializer(page, many=True,
                                            context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BlogPostCreateSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            post = serializer.save(author=request.user)
            if request.data.get('publish'):
                post.is_published = True
                post.published_at = timezone.now()
                post.save()
            return Response(
                BlogPostDetailSerializer(post).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=400)


class BlogPostDetailView(APIView):
    """
    GET    /api/blog/posts/{slug}/  → Public
    PATCH  /api/blog/posts/{slug}/  → Admin
    DELETE /api/blog/posts/{slug}/  → Admin
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdmin()]

    def get(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        post.view_count += 1
        post.save(update_fields=['view_count'])
        return Response(BlogPostDetailSerializer(post).data)

    def patch(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug)
        serializer = BlogPostCreateSerializer(
            post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(BlogPostDetailSerializer(post).data)
        return Response(serializer.errors, status=400)

    def delete(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BlogMediaUploadView(APIView):
    """
    POST /api/blog/posts/{slug}/media/
    Upload image or video to an existing blog post.

    Supported combinations achieved by uploading media separately:
    → Text only         : POST /posts/ with content only
    → Text + Image      : POST /posts/ then POST /posts/{slug}/media/ (image)
    → Text + Video      : POST /posts/ then POST /posts/{slug}/media/ (video)
    → Text+Image+Video  : POST /posts/ then POST media/ twice (image + video)
    → Image only        : POST /posts/ (no content) then POST media/ (image)
    → Video only        : POST /posts/ (no content) then POST media/ (video)
    → Embed YouTube/Vimeo: POST /posts/{slug}/media/ with video_url field
    """
    permission_classes = [IsAdmin]
    parser_classes     = [MultiPartParser, JSONParser]

    def post(self, request, slug):
        post       = get_object_or_404(BlogPost, slug=slug)
        media_type = request.data.get('media_type')  # image | video | video_url

        # ── Embedded Video URL (YouTube / Vimeo) ──────────────────────
        if media_type == 'video_url':
            video_url = request.data.get('video_url', '')
            if not video_url:
                return Response({'error': 'video_url is required.'}, status=400)

            embed_html = self._build_embed_html(video_url)
            media      = BlogMedia.objects.create(
                post      = post,
                media_type= 'video_url',
                video_url = video_url,
                embed_html= embed_html,
                caption   = request.data.get('caption', ''),
                order     = request.data.get('order', 0),
            )
            post.save()  # Triggers post_type update
            return Response(BlogMediaSerializer(media).data, status=201)

        # ── Uploaded File (Image or Video) ────────────────────────────
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided.'}, status=400)

        # Validate MIME type
        mime = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)

        allowed_image_mimes = ['image/jpeg','image/png','image/gif',
                                'image/webp','image/svg+xml']
        allowed_video_mimes = ['video/mp4','video/webm','video/quicktime',
                                'video/avi','video/x-ms-wmv']

        if media_type == 'image' and mime not in allowed_image_mimes:
            return Response({'error': f'Invalid image type: {mime}'}, status=400)
        if media_type == 'video' and mime not in allowed_video_mimes:
            return Response({'error': f'Invalid video type: {mime}'}, status=400)

        # Upload to S3
        file_ext  = file.name.rsplit('.', 1)[-1].lower()
        s3_key    = f"blog/{media_type}s/{uuid.uuid4()}.{file_ext}"
        upload_file_to_s3(file, s3_key, content_type=mime)

        media_data = {
            'post'      : post,
            'media_type': media_type,
            's3_key'    : s3_key,
            'file_name' : file.name,
            'file_size' : file.size,
            'mime_type' : mime,
            'alt_text'  : request.data.get('alt_text', ''),
            'caption'   : request.data.get('caption', ''),
            'order'     : request.data.get('order', 0),
        }

        # Image — get dimensions, create thumbnail
        if media_type == 'image':
            width, height = process_image(file)
            media_data.update({'width': width, 'height': height})

        # Video — extract thumbnail
        if media_type == 'video':
            thumb_key = f"blog/thumbnails/{uuid.uuid4()}.jpg"
            duration  = extract_video_thumbnail(file, thumb_key)
            media_data.update({
                'thumbnail_s3_key': thumb_key,
                'duration_seconds': duration or 0,
            })

        media = BlogMedia.objects.create(**media_data)
        post.save()  # Triggers post_type auto-detection

        return Response(BlogMediaSerializer(media).data, status=201)

    def _build_embed_html(self, url: str) -> str:
        """Generate iframe embed HTML from YouTube or Vimeo URL."""
        import re

        # YouTube
        yt_match = re.search(
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if yt_match:
            vid_id = yt_match.group(1)
            return (f'<iframe width="560" height="315" '
                    f'src="https://www.youtube.com/embed/{vid_id}" '
                    f'frameborder="0" allowfullscreen></iframe>')

        # Vimeo
        vm_match = re.search(r'vimeo\.com/(\d+)', url)
        if vm_match:
            vid_id = vm_match.group(1)
            return (f'<iframe src="https://player.vimeo.com/video/{vid_id}" '
                    f'width="560" height="315" frameborder="0" '
                    f'allowfullscreen></iframe>')

        return f'<video src="{url}" controls></video>'


class BlogMediaDeleteView(APIView):
    """DELETE /api/blog/posts/{slug}/media/{media_id}/"""
    permission_classes = [IsAdmin]

    def delete(self, request, slug, media_id):
        post  = get_object_or_404(BlogPost, slug=slug)
        media = get_object_or_404(BlogMedia, id=media_id, post=post)

        # Delete from S3
        if media.s3_key:
            from utils.s3 import delete_file_from_s3
            delete_file_from_s3(media.s3_key)
        if media.thumbnail_s3_key:
            from utils.s3 import delete_file_from_s3
            delete_file_from_s3(media.thumbnail_s3_key)

        media.delete()
        post.save()  # Triggers post_type recalculation

        return Response(status=204)


class TagListView(APIView):
    """GET /api/blog/tags/  — Public list of all tags."""
    permission_classes = [AllowAny]

    def get(self, request):
        tags = Tag.objects.all().order_by('name')
        return Response(TagSerializer(tags, many=True).data)
```

---

## 5. Document Generation Features

### Models (`documents/models.py`)

```python
from django.db import models
from accounts.models import User
import uuid


class GeneratedDocument(models.Model):

    class DocType(models.TextChoices):
        INCIDENT_REPORT = 'incident_report', 'Incident Report'
        SEARCH_WARRANT  = 'search_warrant',  'Search Warrant'
        ARREST_WARRANT  = 'arrest_warrant',  'Arrest Warrant'

    class NarrativeStyle(models.TextChoices):
        FIRST_PERSON = 'first_person', 'First Person (I, my)'
        THIRD_PERSON = 'third_person', 'Third Person (Officer name)'

    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        GENERATING = 'generating', 'Generating'
        COMPLETED  = 'completed',  'Completed'
        FAILED     = 'failed',     'Failed'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                        editable=False)
    user            = models.ForeignKey(User, on_delete=models.CASCADE,
                                         related_name='documents')
    doc_type        = models.CharField(max_length=30, choices=DocType.choices)
    case_number     = models.CharField(max_length=50, blank=True, db_index=True)
    form_data       = models.JSONField()
    ai_narrative    = models.TextField(blank=True)
    narrative_style = models.CharField(max_length=20,
                                        choices=NarrativeStyle.choices,
                                        default=NarrativeStyle.FIRST_PERSON)
    status          = models.CharField(max_length=20, choices=Status.choices,
                                        default=Status.PENDING)
    error_message   = models.TextField(blank=True)

    # S3 export keys
    s3_pdf_key      = models.CharField(max_length=500, blank=True)
    s3_docx_key     = models.CharField(max_length=500, blank=True)

    # AI metadata
    model_used      = models.CharField(max_length=100, blank=True)
    tokens_used     = models.PositiveIntegerField(default=0)
    generation_time_ms = models.PositiveIntegerField(default=0)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'generated_documents'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['user', 'doc_type']),
            models.Index(fields=['case_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.doc_type} — {self.case_number} ({self.user.email})"
```

### Document Views (`documents/views.py`)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from accounts.permissions import IsOfficer, HasDocumentQuota, IsOwnerOrAdmin
from ai_engine.model_client import ModelClient
from ai_engine.prompt_builder import (
    build_incident_report_prompt,
    build_search_warrant_prompt,
    build_arrest_warrant_prompt,
)
from documents.exporters.pdf import generate_full_incident_report
from documents.exporters.word import generate_incident_report_docx
from .models import GeneratedDocument
from .serializers import GeneratedDocumentSerializer
from utils.audit_log import log_document_generation, log_document_export
import time


PROMPT_BUILDERS = {
    'incident_report': build_incident_report_prompt,
    'search_warrant' : build_search_warrant_prompt,
    'arrest_warrant' : build_arrest_warrant_prompt,
}

EXPORT_GENERATORS = {
    'incident_report': {
        'pdf' : generate_full_incident_report,
        'docx': generate_incident_report_docx,
    },
    # Add search_warrant and arrest_warrant generators similarly
}


class GenerateDocumentView(APIView):
    """
    POST /api/documents/generate/

    Body:
    {
        "doc_type"        : "incident_report",
        "narrative_style" : "first_person",
        "form_data"       : { ...all officer inputs... }
    }
    """
    permission_classes = [IsOfficer, HasDocumentQuota]

    def post(self, request):
        doc_type        = request.data.get('doc_type', 'incident_report')
        narrative_style = request.data.get('narrative_style', 'first_person')
        form_data       = request.data.get('form_data', {})

        if doc_type not in PROMPT_BUILDERS:
            return Response(
                {'error': f'Invalid doc_type. Choose: {list(PROMPT_BUILDERS.keys())}'},
                status=400
            )

        if not form_data:
            return Response({'error': 'form_data is required.'}, status=400)

        # Create pending document record
        doc = GeneratedDocument.objects.create(
            user            = request.user,
            doc_type        = doc_type,
            case_number     = form_data.get('case_number', ''),
            form_data       = form_data,
            narrative_style = narrative_style,
            status          = 'generating',
        )

        # Build prompt + call AI
        try:
            prompt_fn = PROMPT_BUILDERS[doc_type]
            if doc_type == 'incident_report':
                prompt = prompt_fn(form_data, narrative_style)
            else:
                prompt = prompt_fn(form_data)

            start     = time.time()
            client    = ModelClient()
            ai_text   = client.generate(prompt, max_tokens=3000, temperature=0.2)
            elapsed   = int((time.time() - start) * 1000)

            doc.ai_narrative      = ai_text
            doc.status            = 'completed'
            doc.generation_time_ms= elapsed
            doc.model_used        = client.model_name
            doc.save()

            # Increment usage counter
            sub = request.user.subscription
            sub.documents_generated_this_month += 1
            sub.save(update_fields=['documents_generated_this_month'])

            log_document_generation(request.user, doc_type,
                                     form_data.get('case_number',''))

        except Exception as e:
            doc.status        = 'failed'
            doc.error_message = str(e)
            doc.save()
            return Response({'error': f'AI generation failed: {str(e)}'}, status=503)

        return Response({
            'doc_id'      : str(doc.id),
            'ai_narrative': ai_text,
            'doc_type'    : doc_type,
            'case_number' : form_data.get('case_number',''),
            'status'      : 'completed',
        }, status=201)


class RegenerateDocumentView(APIView):
    """POST /api/documents/{id}/regenerate/"""
    permission_classes = [IsOfficer, HasDocumentQuota]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.get(pk=pk, user=request.user)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=404)

        prompt_fn = PROMPT_BUILDERS.get(doc.doc_type)
        if not prompt_fn:
            return Response({'error': 'Unknown document type.'}, status=400)

        if doc.doc_type == 'incident_report':
            prompt = prompt_fn(doc.form_data, doc.narrative_style)
        else:
            prompt = prompt_fn(doc.form_data)

        client        = ModelClient()
        ai_text       = client.generate(prompt, max_tokens=3000, temperature=0.3)
        doc.ai_narrative = ai_text
        doc.save()

        return Response({'doc_id': str(doc.id), 'ai_narrative': ai_text})


class ExportDocumentView(APIView):
    """
    POST /api/documents/{id}/export/

    Body:
    {
        "format"      : "pdf",          // or "docx"
        "edited_text" : "..."           // Optional: officer's edited narrative
    }
    """
    permission_classes = [IsOfficer]

    def post(self, request, pk):
        try:
            doc = GeneratedDocument.objects.get(pk=pk, user=request.user)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=404)

        export_format = request.data.get('format', 'pdf')
        narrative     = request.data.get('edited_text', doc.ai_narrative)
        form_data     = doc.form_data

        filename_base = f"{doc.doc_type}_{form_data.get('case_number','doc')}"

        log_document_export(request.user, str(doc.id), export_format)

        if export_format == 'pdf':
            pdf_bytes = generate_full_incident_report(form_data, narrative)
            response  = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="{filename_base}.pdf"')
            return response

        if export_format == 'docx':
            docx_buf  = generate_incident_report_docx(form_data, narrative)
            response  = HttpResponse(
                docx_buf.getvalue(),
                content_type=(
                    'application/vnd.openxmlformats-'
                    'officedocument.wordprocessingml.document')
            )
            response['Content-Disposition'] = (
                f'attachment; filename="{filename_base}.docx"')
            return response

        return Response({'error': 'Invalid format. Use pdf or docx.'}, status=400)


class DocumentListView(APIView):
    """GET /api/documents/ — Officer's document history."""
    permission_classes = [IsOfficer]

    def get(self, request):
        docs = GeneratedDocument.objects.filter(
            user=request.user
        ).values(
            'id', 'doc_type', 'case_number',
            'status', 'created_at', 'narrative_style'
        )
        return Response(list(docs))


class DocumentDetailView(APIView):
    """GET /api/documents/{id}/ — Full document with narrative."""
    permission_classes = [IsOfficer, IsOwnerOrAdmin]

    def get(self, request, pk):
        try:
            doc = GeneratedDocument.objects.get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        self.check_object_permissions(request, doc)
        return Response(GeneratedDocumentSerializer(doc).data)
```

---

## 6. Subscriptions & Payments

### Models (`subscriptions/models.py`)

```python
from django.db import models
from accounts.models import User
from django.utils import timezone


class Plan(models.Model):
    """
    Subscription plan definitions.
    Managed by admin — not hardcoded.
    """
    name            = models.CharField(max_length=50, unique=True)
    display_name    = models.CharField(max_length=100)
    description     = models.TextField(blank=True)

    # Pricing
    price_monthly   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    price_yearly    = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly  = models.CharField(max_length=100, blank=True)

    # Features / Limits
    document_limit          = models.IntegerField(default=5)   # per month
    can_incident_report     = models.BooleanField(default=True)
    can_search_warrant      = models.BooleanField(default=False)
    can_arrest_warrant      = models.BooleanField(default=False)
    can_export_pdf          = models.BooleanField(default=True)
    can_export_docx         = models.BooleanField(default=False)
    can_save_history        = models.BooleanField(default=False)
    can_regenerate          = models.BooleanField(default=False)
    support_level           = models.CharField(max_length=50,
                                                default='community')  # community/email/priority

    is_active       = models.BooleanField(default=True)
    sort_order      = models.IntegerField(default=0)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'
        ordering = ['sort_order']

    def __str__(self):
        return self.display_name


class Subscription(models.Model):
    """Active subscription for a user."""

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        INACTIVE  = 'inactive',  'Inactive'
        CANCELLED = 'cancelled', 'Cancelled'
        PAST_DUE  = 'past_due',  'Past Due'
        TRIALING  = 'trialing',  'Trialing'
        EXPIRED   = 'expired',   'Expired'

    class BillingPeriod(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        YEARLY  = 'yearly',  'Yearly'

    user            = models.OneToOneField(User, on_delete=models.CASCADE,
                                            related_name='subscription')
    plan            = models.ForeignKey(Plan, on_delete=models.PROTECT,
                                         related_name='subscriptions')
    status          = models.CharField(max_length=20, choices=Status.choices,
                                        default=Status.ACTIVE)
    billing_period  = models.CharField(max_length=10,
                                        choices=BillingPeriod.choices,
                                        default=BillingPeriod.MONTHLY)

    # Stripe
    stripe_customer_id     = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)

    # Period
    current_period_start   = models.DateTimeField(null=True, blank=True)
    current_period_end     = models.DateTimeField(null=True, blank=True)
    trial_end              = models.DateTimeField(null=True, blank=True)
    cancelled_at           = models.DateTimeField(null=True, blank=True)

    # Usage (reset monthly)
    documents_generated_this_month = models.IntegerField(default=0)
    usage_reset_date               = models.DateField(null=True, blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'

    def reset_monthly_usage(self):
        """Called by Celery beat task on the 1st of each month."""
        self.documents_generated_this_month = 0
        self.usage_reset_date = timezone.now().date()
        self.save(update_fields=[
            'documents_generated_this_month', 'usage_reset_date'])

    def __str__(self):
        return f"{self.user.email} — {self.plan.display_name} ({self.status})"


class UsageLog(models.Model):
    """Detailed log of every document generation for billing analysis."""
    user        = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='usage_logs')
    subscription= models.ForeignKey(Subscription, on_delete=models.CASCADE,
                                     null=True)
    doc_type    = models.CharField(max_length=30)
    case_number = models.CharField(max_length=50, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usage_logs'
        ordering = ['-created_at']
```

### Payments & Stripe Webhooks (`payments/webhooks.py`)

```python
import stripe
import logging
from django.conf import settings
from accounts.models import User
from subscriptions.models import Subscription, Plan

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_BY_PRICE_ID = {
    # Monthly prices
    settings.STRIPE_PRICE_BASIC_MONTHLY    : ('basic',      'monthly'),
    settings.STRIPE_PRICE_PRO_MONTHLY      : ('pro',        'monthly'),
    settings.STRIPE_PRICE_ENTERPRISE_MONTHLY: ('enterprise', 'monthly'),
    # Yearly prices
    settings.STRIPE_PRICE_BASIC_YEARLY     : ('basic',      'yearly'),
    settings.STRIPE_PRICE_PRO_YEARLY       : ('pro',        'yearly'),
    settings.STRIPE_PRICE_ENTERPRISE_YEARLY: ('enterprise', 'yearly'),
}


def handle_webhook(payload: bytes, sig_header: str):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise ValueError('Invalid Stripe signature.')

    event_type = event['type']
    data_obj   = event['data']['object']

    handlers = {
        'checkout.session.completed'         : _on_checkout_complete,
        'customer.subscription.updated'      : _on_subscription_updated,
        'customer.subscription.deleted'      : _on_subscription_cancelled,
        'invoice.payment_succeeded'          : _on_payment_succeeded,
        'invoice.payment_failed'             : _on_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        handler(data_obj)
    else:
        logger.info(f"Unhandled Stripe event: {event_type}")


def _on_checkout_complete(session):
    """Activate subscription after successful Stripe checkout."""
    user_id = session['metadata'].get('user_id')
    price_id= session.get('line_items', {})

    # Retrieve full subscription from Stripe
    stripe_sub = stripe.Subscription.retrieve(session['subscription'])
    price_id   = stripe_sub['items']['data'][0]['price']['id']

    plan_name, billing_period = PLAN_BY_PRICE_ID.get(price_id, ('basic', 'monthly'))

    try:
        user = User.objects.get(pk=user_id)
        sub  = user.subscription
        plan = Plan.objects.get(name=plan_name)

        sub.plan                   = plan
        sub.status                 = 'active'
        sub.billing_period         = billing_period
        sub.stripe_subscription_id = stripe_sub['id']
        sub.stripe_customer_id     = stripe_sub['customer']
        sub.current_period_start   = _ts(stripe_sub['current_period_start'])
        sub.current_period_end     = _ts(stripe_sub['current_period_end'])
        sub.documents_generated_this_month = 0
        sub.save()

        logger.info(f"Subscription activated: {user.email} → {plan_name}")

    except User.DoesNotExist:
        logger.error(f"Checkout complete but user {user_id} not found.")


def _on_subscription_updated(stripe_sub):
    try:
        sub = Subscription.objects.get(
            stripe_subscription_id=stripe_sub['id'])
        sub.status               = stripe_sub['status']
        sub.current_period_start = _ts(stripe_sub['current_period_start'])
        sub.current_period_end   = _ts(stripe_sub['current_period_end'])
        sub.save()
    except Subscription.DoesNotExist:
        pass


def _on_subscription_cancelled(stripe_sub):
    try:
        sub = Subscription.objects.get(
            stripe_subscription_id=stripe_sub['id'])
        free_plan    = Plan.objects.get(name='free')
        sub.plan     = free_plan
        sub.status   = 'cancelled'
        sub.save()
        logger.info(f"Subscription cancelled: {sub.user.email}")
    except Subscription.DoesNotExist:
        pass


def _on_payment_succeeded(invoice):
    logger.info(f"Payment succeeded: {invoice['customer_email']} "
                f"${invoice['amount_paid']/100:.2f}")


def _on_payment_failed(invoice):
    try:
        sub = Subscription.objects.get(
            stripe_customer_id=invoice['customer'])
        sub.status = 'past_due'
        sub.save()
        logger.warning(f"Payment failed: {invoice['customer_email']}")
    except Subscription.DoesNotExist:
        pass


def _ts(unix_timestamp):
    """Convert Unix timestamp to Django-aware datetime."""
    from datetime import datetime, timezone
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
```

---

## 7. Admin Panel

### Admin Views (`admin_panel/views.py`)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.models import User, GeneratedDocument
from ai_engine.models import TrainingDocument
from subscriptions.models import Subscription, Plan, UsageLog
from accounts.permissions import IsAdmin
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta


class PlatformStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        now      = timezone.now()
        last_30d = now - timedelta(days=30)
        last_7d  = now - timedelta(days=7)

        return Response({
            'users': {
                'total'    : User.objects.count(),
                'officers' : User.objects.filter(role='officer').count(),
                'new_7d'   : User.objects.filter(
                    created_at__gte=last_7d).count(),
            },
            'documents': {
                'total'    : GeneratedDocument.objects.count(),
                'last_30d' : GeneratedDocument.objects.filter(
                    created_at__gte=last_30d).count(),
                'by_type'  : list(
                    GeneratedDocument.objects
                    .values('doc_type')
                    .annotate(count=Count('id'))
                ),
            },
            'subscriptions': {
                'active'   : Subscription.objects.filter(status='active').count(),
                'by_plan'  : list(
                    Subscription.objects
                    .values('plan__name')
                    .annotate(count=Count('id'))
                ),
            },
            'training_docs': {
                'total'    : TrainingDocument.objects.count(),
                'indexed'  : TrainingDocument.objects.filter(
                    is_indexed=True).count(),
                'by_type'  : list(
                    TrainingDocument.objects
                    .values('doc_type')
                    .annotate(count=Count('id'))
                ),
            },
        })


class PlanManagementView(APIView):
    """GET/POST /api/admin/plans/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        from subscriptions.serializers import PlanSerializer
        plans = Plan.objects.all()
        return Response(PlanSerializer(plans, many=True).data)

    def post(self, request):
        from subscriptions.serializers import PlanSerializer
        serializer = PlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
```

---

## 8. AI Engine

### Model Client (`ai_engine/model_client.py`)

```python
import requests
import json
import boto3
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class ModelClient:
    """
    Unified AI model client.
    Development  → local Ollama (http://localhost:11434)
    Production   → AWS Bedrock Custom Model
    Toggle: USE_LOCAL_MODEL=True/False in .env
    """

    def __init__(self):
        self.use_local  = settings.USE_LOCAL_MODEL
        self.model_name = (
            settings.LOCAL_MODEL_NAME if self.use_local
            else settings.BEDROCK_MODEL_ID
        )

    def generate(self, prompt: str,
                 max_tokens : int   = 3000,
                 temperature: float = 0.2) -> str:
        if self.use_local:
            return self._call_ollama(prompt, max_tokens, temperature)
        return self._call_bedrock(prompt, max_tokens, temperature)

    def _call_ollama(self, prompt, max_tokens, temperature) -> str:
        try:
            response = requests.post(
                f"{settings.LOCAL_MODEL_URL}/api/generate",
                json={
                    "model"  : settings.LOCAL_MODEL_NAME,
                    "prompt" : prompt,
                    "stream" : False,
                    "options": {
                        "temperature" : temperature,
                        "num_predict" : max_tokens,
                        "stop"        : ["[END]", "---END---"],
                    }
                },
                timeout=180
            )
            response.raise_for_status()
            return response.json()['response'].strip()
        except requests.ConnectionError:
            raise RuntimeError(
                "Ollama not running. Start with: ollama serve")

    def _call_bedrock(self, prompt, max_tokens, temperature) -> str:
        client = boto3.client(
            'bedrock-runtime',
            region_name          = settings.BEDROCK_REGION,
            aws_access_key_id    = settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY,
        )
        # Llama 3 format
        formatted = (
            f"<|begin_of_text|>"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"{prompt}"
            f"<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n"
        )
        response = client.invoke_model(
            modelId     = settings.BEDROCK_MODEL_ID,
            contentType = 'application/json',
            accept      = 'application/json',
            body        = json.dumps({
                'prompt'      : formatted,
                'max_gen_len' : max_tokens,
                'temperature' : temperature,
                'top_p'       : 0.9,
            })
        )
        result = json.loads(response['body'].read())
        return result.get('generation', '').strip()
```

---

## 9. URL Configuration

### Root URLs (`core/urls.py`)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/',          admin.site.urls),

    # Authentication & Users
    path('api/auth/',       include('accounts.urls')),

    # Document Generation
    path('api/documents/',  include('documents.urls')),

    # AI Training (admin)
    path('api/ai/',         include('ai_engine.urls')),

    # Blog
    path('api/blog/',       include('blog.urls')),

    # Subscriptions
    path('api/subscriptions/', include('subscriptions.urls')),

    # Payments
    path('api/payments/',   include('payments.urls')),

    # Admin Panel
    path('api/admin-panel/',include('admin_panel.urls')),

    # API Docs (dev only)
    path('api/schema/',     include('drf_spectacular.urls')),
]
```

### Per-App URLs

```python
# accounts/urls.py
from django.urls import path
from .views import RegisterView, ProfileView, UserListView

urlpatterns = [
    path('register/',           RegisterView.as_view()),
    path('profile/',            ProfileView.as_view()),
    path('users/',              UserListView.as_view()),
]

# ─────────────────────────────────────

# blog/urls.py
from django.urls import path
from .views import (
    BlogPostListView, BlogPostDetailView,
    BlogMediaUploadView, BlogMediaDeleteView, TagListView,
)

urlpatterns = [
    path('posts/',                          BlogPostListView.as_view()),
    path('posts/<slug:slug>/',              BlogPostDetailView.as_view()),
    path('posts/<slug:slug>/media/',        BlogMediaUploadView.as_view()),
    path('posts/<slug:slug>/media/<int:media_id>/', BlogMediaDeleteView.as_view()),
    path('tags/',                           TagListView.as_view()),
]

# ─────────────────────────────────────

# documents/urls.py
from django.urls import path
from .views import (
    GenerateDocumentView, RegenerateDocumentView,
    ExportDocumentView, DocumentListView, DocumentDetailView,
)

urlpatterns = [
    path('',                        DocumentListView.as_view()),
    path('generate/',               GenerateDocumentView.as_view()),
    path('<uuid:pk>/',              DocumentDetailView.as_view()),
    path('<uuid:pk>/regenerate/',   RegenerateDocumentView.as_view()),
    path('<uuid:pk>/export/',       ExportDocumentView.as_view()),
]

# ─────────────────────────────────────

# subscriptions/urls.py
from django.urls import path
from .views import PlanListView, SubscriptionStatusView, CancelSubscriptionView

urlpatterns = [
    path('plans/',          PlanListView.as_view()),
    path('status/',         SubscriptionStatusView.as_view()),
    path('cancel/',         CancelSubscriptionView.as_view()),
]

# ─────────────────────────────────────

# payments/urls.py
from django.urls import path
from .views import CreateCheckoutSessionView, StripeWebhookView, BillingHistoryView

urlpatterns = [
    path('create-checkout/',    CreateCheckoutSessionView.as_view()),
    path('webhook/',            StripeWebhookView.as_view()),
    path('billing-history/',    BillingHistoryView.as_view()),
]

# ─────────────────────────────────────

# ai_engine/urls.py
from django.urls import path
from .views import UploadTrainingDocumentView, TrainingDocumentListView

urlpatterns = [
    path('training-docs/',          TrainingDocumentListView.as_view()),
    path('training-docs/upload/',   UploadTrainingDocumentView.as_view()),
]

# ─────────────────────────────────────

# admin_panel/urls.py
from django.urls import path
from .views import PlatformStatsView, PlanManagementView

urlpatterns = [
    path('stats/',  PlatformStatsView.as_view()),
    path('plans/',  PlanManagementView.as_view()),
]
```

---

## 10. Settings Structure

### `core/settings/base.py` (key sections)

```python
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',
    'storages',
    'django_celery_beat',
    'django_celery_results',
    'axes',
    'drf_spectacular',

    # Local apps
    'accounts',
    'blog',
    'documents',
    'ai_engine',
    'subscriptions',
    'payments',
    'admin_panel',
]

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS'    : 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardPagination',
    'PAGE_SIZE'               : 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# File upload size limit — 500MB for video
DATA_UPLOAD_MAX_MEMORY_SIZE  = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE  = 524288000
```

---

## 11. Database Models Summary

```
┌─────────────────────────────────────────────────────────┐
│ POSTGRESQL TABLES                                        │
├─────────────────────┬───────────────────────────────────┤
│ users               │ Custom user, Firebase UID, role   │
│ subscriptions       │ Plan, status, Stripe IDs, usage   │
│ plans               │ Plan definitions, limits, prices  │
│ usage_logs          │ Per-generation billing log        │
│ generated_documents │ AI docs, form data, narratives    │
│ training_documents  │ Admin-uploaded sample docs        │
│ document_chunks     │ Text chunks + pgvector embeddings │
│ blog_posts          │ Posts with all media types        │
│ blog_media          │ Images, videos, embeds per post   │
│ blog_tags           │ Tags for filtering                │
│ payments            │ Stripe payment records            │
│ invoices            │ Invoice history                   │
└─────────────────────┴───────────────────────────────────┘
```

---

## 12. Environment Variables (.env)

```bash
# ════════════════════════════════
# DJANGO
# ════════════════════════════════
DJANGO_SECRET_KEY=your-50-char-secret-key-here
DEBUG=True
DJANGO_SETTINGS_MODULE=core.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000

# ════════════════════════════════
# DATABASE — PostgreSQL
# ════════════════════════════════
DB_NAME=law_enforcement_db
DB_USER=le_user
DB_PASSWORD=your_strong_password
DB_HOST=localhost
DB_PORT=5432

# ════════════════════════════════
# DATABASE — MongoDB
# ════════════════════════════════
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=le_documents

# ════════════════════════════════
# REDIS
# ════════════════════════════════
REDIS_URL=redis://localhost:6379/0

# ════════════════════════════════
# AWS
# ════════════════════════════════
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-le-platform-bucket
AWS_S3_BUCKET_REGION=us-east-1

# ════════════════════════════════
# AI MODEL
# ════════════════════════════════
USE_LOCAL_MODEL=True
LOCAL_MODEL_URL=http://localhost:11434
LOCAL_MODEL_NAME=llama3.1:8b
BEDROCK_MODEL_ID=arn:aws:bedrock:us-east-1::foundation-model/your-model
BEDROCK_REGION=us-east-1

# ════════════════════════════════
# FIREBASE
# ════════════════════════════════
FIREBASE_CREDENTIALS_PATH=./firebase_credentials.json

# ════════════════════════════════
# STRIPE
# ════════════════════════════════
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC_MONTHLY=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_...
STRIPE_PRICE_BASIC_YEARLY=price_...
STRIPE_PRICE_PRO_YEARLY=price_...
STRIPE_PRICE_ENTERPRISE_YEARLY=price_...

# ════════════════════════════════
# EMAIL (AWS SES)
# ════════════════════════════════
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-smtp-username
EMAIL_HOST_PASSWORD=your-ses-smtp-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

---

## 13. Celery & Background Tasks

### `core/celery.py`

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
app = Celery('law_enforcement')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    # Reset document usage counter on 1st of each month
    'reset-monthly-usage': {
        'task'    : 'subscriptions.tasks.reset_monthly_usage',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
    # Clean up failed document records older than 30 days
    'cleanup-failed-docs': {
        'task'    : 'documents.tasks.cleanup_failed_documents',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

### Task Examples

```python
# subscriptions/tasks.py
from celery import shared_task
from .models import Subscription

@shared_task
def reset_monthly_usage():
    """Reset document counter for all active subscriptions."""
    count = 0
    for sub in Subscription.objects.filter(status='active'):
        sub.reset_monthly_usage()
        count += 1
    return f"Reset usage for {count} subscriptions."


# ai_engine/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def index_training_document(self, training_doc_id: int):
    """
    Async task: generate embeddings for a training document.
    Called after admin uploads a doc — avoids blocking the HTTP request.
    """
    try:
        from ai_engine.models import TrainingDocument, DocumentChunk
        from ai_engine.embeddings import EmbeddingClient
        from ai_engine.document_parser import chunk_text

        doc      = TrainingDocument.objects.get(pk=training_doc_id)
        chunks   = chunk_text(doc.raw_text)
        embedder = EmbeddingClient()

        DocumentChunk.objects.filter(training_doc=doc).delete()

        bulk = []
        for i, text in enumerate(chunks):
            emb = embedder.embed(text)
            bulk.append(DocumentChunk(
                training_doc=doc, doc_type=doc.doc_type,
                chunk_index=i, text=text, embedding=emb,
            ))
        DocumentChunk.objects.bulk_create(bulk)

        doc.chunk_count = len(bulk)
        doc.is_indexed  = True
        doc.save()

        return f"Indexed {len(bulk)} chunks for doc {training_doc_id}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## 14. Storage (S3)

### `utils/s3.py`

```python
import boto3
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

s3_client = boto3.client(
    's3',
    region_name          = settings.AWS_S3_BUCKET_REGION,
    aws_access_key_id    = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY,
)

BUCKET = settings.AWS_S3_BUCKET


def upload_file_to_s3(file_obj, s3_key: str,
                       content_type: str = 'application/octet-stream') -> str:
    s3_client.upload_fileobj(
        file_obj, BUCKET, s3_key,
        ExtraArgs={
            'ContentType'         : content_type,
            'ServerSideEncryption': 'AES256',  # CJIS requirement
        }
    )
    logger.info(f"Uploaded to S3: {s3_key}")
    return s3_key


def upload_bytes_to_s3(data: bytes, s3_key: str,
                        content_type: str = 'application/octet-stream') -> str:
    import io
    return upload_file_to_s3(io.BytesIO(data), s3_key, content_type)


def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a time-limited URL for private S3 files."""
    return s3_client.generate_presigned_url(
        'get_object',
        Params    = {'Bucket': BUCKET, 'Key': s3_key},
        ExpiresIn = expires_in,
    )


def delete_file_from_s3(s3_key: str) -> bool:
    try:
        s3_client.delete_object(Bucket=BUCKET, Key=s3_key)
        return True
    except Exception as e:
        logger.error(f"S3 delete failed for {s3_key}: {e}")
        return False
```

---

## 15. Docker & Deployment Files

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev build-essential \
    libmagic1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120"]
```

### `docker-compose.yml` (development)

```yaml
version: '3.9'

services:

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB      : law_enforcement_db
      POSTGRES_USER    : le_user
      POSTGRES_PASSWORD: devpassword123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: core.settings.development
    depends_on:
      - db
      - mongo
      - redis

  celery:
    build: .
    command: celery -A core worker --loglevel=info
    volumes:
      - .:/app
    env_file: .env
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - .:/app
    env_file: .env
    depends_on:
      - db
      - redis

  flower:
    build: .
    command: celery -A core flower --port=5555
    ports:
      - "5555:5555"
    env_file: .env
    depends_on:
      - redis

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  postgres_data:
  mongo_data:
  ollama_data:
```

### `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*.pyo
.Python
venv/
env/
.venv/

# Django
*.log
local_settings.py
db.sqlite3
media/
staticfiles/

# Environment
.env
.env.*
!.env.example
firebase_credentials.json

# AI / ML
fine_tuned_model/
training_data.jsonl
*.gguf
*.safetensors
*.bin

# Docker
.docker/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/
```

---

## Quick Start Commands

```bash
# 1. Clone + setup
git clone <repo-url> && cd law-enforcement-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Database
createdb law_enforcement_db
python manage.py migrate
python manage.py createsuperuser

# 3. Start services
ollama pull llama3.1:8b && ollama serve &
redis-server &
celery -A core worker --loglevel=info &
celery -A core beat --loglevel=info &

# 4. Run server
python manage.py runserver

# OR with Docker (one command):
docker-compose up --build

# 5. Run tests
pytest --cov=. --cov-report=html

# 6. API docs (dev)
# Visit: http://localhost:8000/api/schema/swagger-ui/
```

---

*Law Enforcement Workflow Automation System — Backend Structure v1.0*
*Web Chrome · Towhidul Islam · June 2026*

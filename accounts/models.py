from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """
    Custom user model for law enforcement officers and platform admins.

    Authentication is self-hosted: email + password, issuing JWTs
    (djangorestframework-simplejwt). Email is the login identifier — there is
    no username. Gmail SMTP handles email verification and password resets.
    """

    class Role(models.TextChoices):
        FREE = 'free', 'Free User'
        OFFICER = 'officer', 'Law Enforcement Officer'
        ADMIN = 'admin', 'Platform Admin'

    # ── Identity (email replaces username) ──────────────────────────────
    username = None
    email = models.EmailField(unique=True)

    # ── Role ────────────────────────────────────────────────────────────
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.FREE
    )

    # ── Officer profile (auto-injected into generated documents) ─────────
    badge_number = models.CharField(max_length=50, blank=True)
    department_name = models.CharField(max_length=200, blank=True)
    department_address = models.TextField(blank=True)
    department_state = models.CharField(max_length=50, blank=True)
    ori = models.CharField(max_length=20, blank=True)  # ORI: agency identifier
    phone_number = models.CharField(max_length=20, blank=True)
    rank = models.CharField(max_length=100, blank=True)
    division = models.CharField(max_length=100, blank=True)

    # ── Email verification (via SMTP, Step 5) ───────────────────────────
    email_verified = models.BooleanField(default=False)

    # ── Officer vetting (admin-approved, distinct from email verification) ─
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verified_users',
    )

    # ── Timestamps ──────────────────────────────────────────────────────
    last_active = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email + password are prompted automatically

    objects = UserManager()

    class Meta:
        db_table = 'users'
        indexes = [
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
        # `subscription` relation is added in Step 4; guard until then.
        sub = getattr(self, 'subscription', None)
        return bool(sub and sub.status == 'active')

    @property
    def can_generate_document(self):
        sub = getattr(self, 'subscription', None)
        if not sub:
            return False
        return sub.documents_generated_this_month < sub.plan.document_limit

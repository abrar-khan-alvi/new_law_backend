from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import UserManager


class JurisdictionProfile(models.Model):
    """
    Shared, reusable jurisdiction-level defaults (e.g. "Georgia — State") that many
    Agencies in the same state/jurisdiction can inherit from, instead of every new
    agency re-entering the same statutes and formatting rules. Adding a new state,
    county, or federal district should mean creating one of these, not new code.
    """
    class JurisdictionType(models.TextChoices):
        FEDERAL = 'federal', 'Federal'
        STATE = 'state', 'State'
        MUNICIPAL = 'municipal', 'Municipal/County'

    name = models.CharField(max_length=255, unique=True, help_text='e.g. "Georgia — State"')
    jurisdiction_type = models.CharField(max_length=50, choices=JurisdictionType.choices)
    state = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    default_legal_citations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jurisdiction_profiles'
        verbose_name_plural = 'Jurisdiction Profiles'
        ordering = ['name']

    def __str__(self):
        return self.name


class Agency(models.Model):
    """
    Jurisdiction and configuration profile for an agency.
    """
    class JurisdictionType(models.TextChoices):
        FEDERAL = 'federal', 'Federal'
        STATE = 'state', 'State'
        MUNICIPAL = 'municipal', 'Municipal/County'

    name = models.CharField(max_length=255, unique=True)
    jurisdiction_type = models.CharField(
        max_length=50, choices=JurisdictionType.choices, default=JurisdictionType.STATE
    )
    jurisdiction_profile = models.ForeignKey(
        JurisdictionProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='agencies',
        help_text='Shared state/federal defaults (citations, formatting) this agency inherits.',
    )
    state = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    court_name = models.CharField(max_length=255, blank=True)
    judicial_district = models.CharField(max_length=255, blank=True)
    division = models.CharField(max_length=100, blank=True)
    court_caption = models.CharField(max_length=255, blank=True)
    judge_title = models.CharField(max_length=100, blank=True)
    prosecuting_authority = models.CharField(max_length=255, blank=True)
    case_number_format = models.CharField(max_length=100, blank=True)
    ori = models.CharField(max_length=50, blank=True)
    default_legal_citations = models.TextField(blank=True)
    seal_image_key = models.CharField(
        max_length=500, blank=True, help_text='Storage key for the agency seal/logo (utils.storage).'
    )

    # Agency Configuration Wizard — review workflow toggles (requirement #4).
    requires_supervisor_review = models.BooleanField(default=False)
    requires_prosecutor_review = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agencies'
        verbose_name_plural = 'Agencies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def effective_legal_citations(self) -> str:
        """This agency's citations, falling back to its jurisdiction profile's."""
        return self.default_legal_citations or (
            self.jurisdiction_profile.default_legal_citations if self.jurisdiction_profile else ''
        )



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
    agency = models.ForeignKey(
        Agency, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='officers', help_text="The jurisdiction configuration for this user."
    )
    # Supervisor capability (scoped to this user's own agency) — not a separate
    # Role, so existing free/officer/admin permission checks are unaffected.
    is_supervisor = models.BooleanField(default=False)

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
        return bool(sub and sub.status in ('active', 'trialing'))

    def can_generate(self, doc_type: str) -> bool:
        """
        Informational check only — a non-atomic peek at whether this doc
        type's quota bucket has room. The actual generate/regenerate views use
        Subscription.try_reserve_quota() to atomically check-and-reserve, so
        this is safe to use for UI/status display but never as the sole gate
        before a real reservation.
        """
        sub = getattr(self, 'subscription', None)
        if not sub:
            return False
        counter_field, limit = sub._quota_field_for(doc_type)
        if limit is None:
            return True
        return getattr(sub, counter_field) < limit


class EmailOTP(models.Model):
    """
    A numeric one-time code emailed to a user for email verification or password
    reset. The code itself is never stored — only an HMAC hash (see accounts.otp).
    """

    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = 'email_verification', 'Email Verification'
        PASSWORD_RESET = 'password_reset', 'Password Reset'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps',
    )
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    code_hash = models.CharField(max_length=64)
    attempts = models.PositiveSmallIntegerField(default=0)
    used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_otps'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'purpose', 'used'])]

    def __str__(self):
        return f"{self.purpose} for {self.user_id} ({'used' if self.used else 'active'})"

    def is_expired(self):
        return timezone.now() > self.expires_at

from django.conf import settings
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    """
    Subscription plan definitions. Admin-managed (not hardcoded) — the seed
    command creates sensible defaults that admins can edit later.
    """
    name = models.CharField(max_length=50, unique=True)          # machine key, e.g. 'pro'
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # ── Pricing ─────────────────────────────────────────────────────────
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=100, blank=True)

    # ── Features / limits ───────────────────────────────────────────────
    document_limit = models.IntegerField(default=5)             # per month
    can_incident_report = models.BooleanField(default=True)
    can_search_warrant = models.BooleanField(default=False)
    can_arrest_warrant = models.BooleanField(default=False)
    can_export_pdf = models.BooleanField(default=True)
    can_export_docx = models.BooleanField(default=False)
    can_save_history = models.BooleanField(default=False)
    can_regenerate = models.BooleanField(default=False)
    support_level = models.CharField(max_length=50, default='community')  # community/email/priority

    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'
        ordering = ['sort_order']

    def __str__(self):
        return self.display_name

    def allows_doc_type(self, doc_type: str) -> bool:
        """Used by document generation to gate modules by plan (Step 8)."""
        return {
            'incident_report': self.can_incident_report,
            'search_warrant': self.can_search_warrant,
            'arrest_warrant': self.can_arrest_warrant,
        }.get(doc_type, False)


class Subscription(models.Model):
    """A user's current subscription state."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        CANCELLED = 'cancelled', 'Cancelled'
        PAST_DUE = 'past_due', 'Past Due'
        TRIALING = 'trialing', 'Trialing'
        EXPIRED = 'expired', 'Expired'

    class BillingPeriod(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='subscription',
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name='subscriptions',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE,
    )
    billing_period = models.CharField(
        max_length=10, choices=BillingPeriod.choices, default=BillingPeriod.MONTHLY,
    )

    # ── Stripe (Phase 4) ────────────────────────────────────────────────
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)

    # ── Billing period ──────────────────────────────────────────────────
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # ── Usage (reset monthly) ───────────────────────────────────────────
    documents_generated_this_month = models.IntegerField(default=0)
    usage_reset_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'

    def __str__(self):
        return f"{self.user.email} — {self.plan.display_name} ({self.status})"

    def reset_monthly_usage(self):
        """Called by the Celery beat task on the 1st of each month (Phase 5)."""
        self.documents_generated_this_month = 0
        self.usage_reset_date = timezone.now().date()
        self.save(update_fields=['documents_generated_this_month', 'usage_reset_date'])


class UsageLog(models.Model):
    """Per-generation record for billing analysis and auditing."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='usage_logs',
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, null=True, blank=True,
    )
    doc_type = models.CharField(max_length=30)
    case_number = models.CharField(max_length=50, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usage_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.doc_type} ({self.created_at:%Y-%m-%d})"

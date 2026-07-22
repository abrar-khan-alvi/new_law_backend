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
    # Incident reports per month. NULL means unlimited (not a magic-number sentinel).
    document_limit = models.PositiveIntegerField(
        null=True, blank=True, default=5,
        help_text='Incident reports per month. Leave blank for unlimited.',
    )
    # Search + arrest warrants per month, combined. NULL means unlimited — the
    # policy is that warrant generation is never hard-capped on a paying plan,
    # since a missed court deadline is a far worse failure than extra AI cost.
    warrant_document_limit = models.PositiveIntegerField(
        null=True, blank=True, default=None,
        help_text='Search + arrest warrants per month, combined. Leave blank for unlimited.',
    )
    can_incident_report = models.BooleanField(default=True)
    can_search_warrant = models.BooleanField(default=False)
    can_arrest_warrant = models.BooleanField(default=False)
    can_export_pdf = models.BooleanField(default=True)
    can_export_docx = models.BooleanField(default=False)
    can_save_history = models.BooleanField(default=False)
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
    # True once the user has clicked Cancel — subscription stays active/usable
    # through current_period_end, then the Stripe webhook downgrades to free.
    cancel_at_period_end = models.BooleanField(default=False)
    # One free trial per account, ever — prevents trial-cycling by re-signup abuse
    # (a new User always gets a fresh Subscription row, so this can't be reset).
    has_used_trial = models.BooleanField(default=False)

    # ── Usage (reset monthly) ───────────────────────────────────────────
    # Separate counters: incident reports and warrants have independent
    # quotas (Plan.document_limit vs Plan.warrant_document_limit), so they
    # can't share one counter without one doc type silently eating the
    # other's allowance.
    documents_generated_this_month = models.IntegerField(default=0)  # incident reports
    warrants_generated_this_month = models.IntegerField(default=0)   # search + arrest, combined —
    # this is what's actually checked against Plan.warrant_document_limit; kept
    # unchanged so the tested quota-enforcement logic below is untouched.
    # Per-type breakdown, display-only — these never gate quota on their own,
    # they just mirror which of the two warrant types the combined count above
    # came from, so the UI can show "N search / M arrest" instead of one blob.
    search_warrants_generated_this_month = models.IntegerField(default=0)
    arrest_warrants_generated_this_month = models.IntegerField(default=0)
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
        self.warrants_generated_this_month = 0
        self.search_warrants_generated_this_month = 0
        self.arrest_warrants_generated_this_month = 0
        self.usage_reset_date = timezone.now().date()
        self.save(update_fields=[
            'documents_generated_this_month', 'warrants_generated_this_month',
            'search_warrants_generated_this_month', 'arrest_warrants_generated_this_month',
            'usage_reset_date',
        ])

    _WARRANT_DOC_TYPES = {'search_warrant', 'arrest_warrant'}
    # doc_type -> its display-only per-type counter field (see field comments above).
    _WARRANT_SUBCOUNTER = {
        'search_warrant': 'search_warrants_generated_this_month',
        'arrest_warrant': 'arrest_warrants_generated_this_month',
    }

    def _quota_field_for(self, doc_type: str):
        """(counter_field_name, limit) for the quota bucket a doc_type draws from."""
        if doc_type == 'incident_report':
            return 'documents_generated_this_month', self.plan.document_limit
        if doc_type in self._WARRANT_DOC_TYPES:
            return 'warrants_generated_this_month', self.plan.warrant_document_limit
        raise ValueError(f'Unrecognized doc_type for quota accounting: {doc_type!r}')

    def try_reserve_quota(self, doc_type: str) -> bool:
        """
        Atomically increments the counter for this doc_type's quota bucket only
        if still under that bucket's limit — a single conditional UPDATE, so
        two concurrent requests can't both slip through a plain read-then-write
        check (TOCTOU). Returns whether a slot was reserved; call
        release_quota(doc_type) if the generation that follows fails, so a
        failed attempt doesn't cost the user their quota. A limit of None
        means unlimited — always reserves without a WHERE condition.
        """
        counter_field, limit = self._quota_field_for(doc_type)
        sub_field = self._WARRANT_SUBCOUNTER.get(doc_type)
        qs = Subscription.objects.filter(pk=self.pk)
        if limit is not None:
            qs = qs.filter(**{f'{counter_field}__lt': limit})
        update_kwargs = {counter_field: models.F(counter_field) + 1}
        if sub_field:
            update_kwargs[sub_field] = models.F(sub_field) + 1
        updated = qs.update(**update_kwargs)
        if updated:
            self.refresh_from_db(fields=list(update_kwargs))
        return bool(updated)

    def release_quota(self, doc_type: str):
        """Undo a reservation from try_reserve_quota() after a failed generation."""
        counter_field, _ = self._quota_field_for(doc_type)
        sub_field = self._WARRANT_SUBCOUNTER.get(doc_type)
        update_kwargs = {counter_field: models.F(counter_field) - 1}
        if sub_field:
            update_kwargs[sub_field] = models.F(sub_field) - 1
        Subscription.objects.filter(pk=self.pk).update(**update_kwargs)
        self.refresh_from_db(fields=list(update_kwargs))


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

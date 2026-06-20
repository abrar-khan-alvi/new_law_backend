from django.conf import settings
from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments',
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.amount} {self.currency} ({self.status})'


class Invoice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices',
    )
    stripe_invoice_id = models.CharField(max_length=255, blank=True, db_index=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=30, blank=True)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    hosted_invoice_url = models.URLField(blank=True)
    invoice_pdf = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f'Invoice {self.stripe_invoice_id or self.id} — {self.user.email}'

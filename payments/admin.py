from django.contrib import admin

from .models import Invoice, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('user__email', 'stripe_payment_intent_id', 'stripe_charge_id')
    raw_id_fields = ('user',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_invoice_id', 'amount_paid', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'stripe_invoice_id')
    raw_id_fields = ('user',)

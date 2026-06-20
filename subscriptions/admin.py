from django.contrib import admin

from .models import Plan, Subscription, UsageLog


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'display_name', 'name', 'price_monthly', 'price_yearly',
        'document_limit', 'is_active', 'sort_order',
    )
    list_filter = ('is_active', 'support_level')
    search_fields = ('name', 'display_name')
    ordering = ('sort_order',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'plan', 'status', 'billing_period',
        'documents_generated_this_month', 'current_period_end',
    )
    list_filter = ('status', 'billing_period', 'plan')
    search_fields = ('user__email', 'stripe_customer_id', 'stripe_subscription_id')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'doc_type', 'case_number', 'tokens_used', 'created_at')
    list_filter = ('doc_type',)
    search_fields = ('user__email', 'case_number')
    raw_id_fields = ('user', 'subscription')
    readonly_fields = ('created_at',)

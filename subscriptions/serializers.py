from rest_framework import serializers

from .models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'display_name', 'description',
            'price_monthly', 'price_yearly',
            'document_limit', 'warrant_document_limit',
            'can_incident_report', 'can_search_warrant',
            'can_arrest_warrant', 'can_export_pdf', 'can_export_docx',
            'can_save_history', 'support_level',
            'is_active', 'sort_order',
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'status', 'billing_period',
            'current_period_start', 'current_period_end', 'trial_end',
            'cancel_at_period_end', 'has_used_trial',
            'documents_generated_this_month', 'warrants_generated_this_month',
            'search_warrants_generated_this_month', 'arrest_warrants_generated_this_month',
            'usage_reset_date',
            'created_at',
        ]

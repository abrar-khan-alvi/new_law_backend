from django.urls import path

from .views import (
    BillingHistoryView,
    CreateCheckoutSessionView,
    StripeWebhookView,
)

urlpatterns = [
    path('create-checkout/', CreateCheckoutSessionView.as_view()),
    path('webhook/', StripeWebhookView.as_view()),
    path('billing-history/', BillingHistoryView.as_view()),
]

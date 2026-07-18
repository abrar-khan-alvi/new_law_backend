from django.urls import path

from .views import (
    CancelSubscriptionView,
    PlanListView,
    StartTrialView,
    SubscriptionStatusView,
)

urlpatterns = [
    path('plans/', PlanListView.as_view()),
    path('status/', SubscriptionStatusView.as_view()),
    path('start-trial/', StartTrialView.as_view()),
    path('cancel/', CancelSubscriptionView.as_view()),
]

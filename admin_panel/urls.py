from django.urls import path

from .views import (
    PlanDetailView,
    PlanManagementView,
    PlatformStatsView,
    UserDetailView,
    UserManagementView,
)

urlpatterns = [
    path('stats/', PlatformStatsView.as_view()),
    path('plans/', PlanManagementView.as_view()),
    path('plans/<int:pk>/', PlanDetailView.as_view()),
    path('users/', UserManagementView.as_view()),
    path('users/<int:pk>/', UserDetailView.as_view()),
]

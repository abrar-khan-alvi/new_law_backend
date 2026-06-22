from django.urls import path

from .views import (
    DocumentDetailAdminView,
    DocumentManagementView,
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
    path('documents/', DocumentManagementView.as_view()),
    path('documents/<uuid:pk>/', DocumentDetailAdminView.as_view()),
]

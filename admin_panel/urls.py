from django.urls import path

from .views import (
    ActivityLogView,
    AgencyDetailView,
    AgencyListCreateView,
    AgencySealUploadView,
    DocumentDetailAdminView,
    DocumentManagementView,
    JurisdictionProfileDetailView,
    JurisdictionProfileListCreateView,
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
    path('jurisdiction-profiles/', JurisdictionProfileListCreateView.as_view()),
    path('jurisdiction-profiles/<int:pk>/', JurisdictionProfileDetailView.as_view()),
    path('agencies/', AgencyListCreateView.as_view()),
    path('agencies/<int:pk>/', AgencyDetailView.as_view()),
    path('agencies/<int:pk>/seal/', AgencySealUploadView.as_view()),
    path('activity/', ActivityLogView.as_view()),
]

from django.urls import path

from .views import (
    DocumentDetailView,
    DocumentListView,
    ExportDocumentView,
    GenerateDocumentView,
    ProsecutorReviewView,
    RegenerateDocumentView,
    SignDocumentView,
    SupervisorReviewView,
)

urlpatterns = [
    path('', DocumentListView.as_view()),
    path('generate/', GenerateDocumentView.as_view()),
    path('<uuid:pk>/', DocumentDetailView.as_view()),
    path('<uuid:pk>/regenerate/', RegenerateDocumentView.as_view()),
    path('<uuid:pk>/export/', ExportDocumentView.as_view()),
    path('<uuid:pk>/supervisor-review/', SupervisorReviewView.as_view()),
    path('<uuid:pk>/prosecutor-review/', ProsecutorReviewView.as_view()),
    path('<uuid:pk>/sign/', SignDocumentView.as_view()),
]

from django.urls import path

from .views import (
    DocumentDetailView,
    DocumentListView,
    GenerateDocumentView,
    RegenerateDocumentView,
)

urlpatterns = [
    path('', DocumentListView.as_view()),
    path('generate/', GenerateDocumentView.as_view()),
    path('<uuid:pk>/', DocumentDetailView.as_view()),
    path('<uuid:pk>/regenerate/', RegenerateDocumentView.as_view()),
    # Export endpoint is added in Step 9 (exporters):
    # path('<uuid:pk>/export/', ExportDocumentView.as_view()),
]

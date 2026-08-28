from django.urls import path

from .views import TrainingDocumentDetailView, TrainingDocumentListView, UploadTrainingDocumentView

urlpatterns = [
    path('training-docs/', TrainingDocumentListView.as_view()),
    path('training-docs/<int:pk>/', TrainingDocumentDetailView.as_view()),
    path('training-docs/upload/', UploadTrainingDocumentView.as_view()),
]

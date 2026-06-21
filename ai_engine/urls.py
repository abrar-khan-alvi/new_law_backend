from django.urls import path

from .views import TrainingDocumentListView, UploadTrainingDocumentView

urlpatterns = [
    path('training-docs/', TrainingDocumentListView.as_view()),
    path('training-docs/upload/', UploadTrainingDocumentView.as_view()),
]

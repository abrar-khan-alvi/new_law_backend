from django.urls import path

from .views import (
    BlogMediaDeleteView,
    BlogMediaUploadView,
    BlogPostDetailView,
    BlogPostListView,
    TagListView,
)

urlpatterns = [
    path('posts/', BlogPostListView.as_view()),
    path('posts/<slug:slug>/', BlogPostDetailView.as_view()),
    path('posts/<slug:slug>/media/', BlogMediaUploadView.as_view()),
    path('posts/<slug:slug>/media/<int:media_id>/', BlogMediaDeleteView.as_view()),
    path('tags/', TagListView.as_view()),
]

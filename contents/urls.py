from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubjectContentViewSet,
    ContentAttachmentViewSet
)

router = DefaultRouter()

router.register(r'subject-content', SubjectContentViewSet, basename='subject-content')
router.register(r'content-attachments', ContentAttachmentViewSet, basename='content-attachments')

urlpatterns = [
    path('', include(router.urls)),
]
# subject/urls.py (لا تغييرات)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('subjects', views.SubjectViewSet)
urlpatterns = [
    path('', include(router.urls)),
]
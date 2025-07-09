# communication/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsActivityViewSet


router = DefaultRouter()

#
router.register(r'news-activities', NewsActivityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
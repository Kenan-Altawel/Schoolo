from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('classes', views.ClassViewSet)
urlpatterns = [
    path('', include(router.urls)), 
    
]
# exams/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'exams', ExamViewSet, basename='exam')

urlpatterns = [
    path('', include(router.urls)),
    path('exams/<int:pk>/conduct/', ExamConductView.as_view(), name='exam-conduct'),
]
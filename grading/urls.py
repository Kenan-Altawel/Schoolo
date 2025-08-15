# exams/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'grades', GradeViewSet, basename='grade') # تم إضافة هذا السطر

urlpatterns = [
    path('', include(router.urls)),
    path('exams/<int:pk>/conduct/', ExamConductView.as_view(), name='exam-conduct'),
]
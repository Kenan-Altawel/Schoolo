# teachers/urls.py

from django.urls import path
from .views import *

urlpatterns = [
    path('teacher-profile/', TeacherProfileUpdateView.as_view(), name='teacher-profile-update'),
    path('show-teachers/', TeacherListView.as_view(), name='teacher-list'),
    path('<int:teacher_id>/subjects/', TeacherSubjectsListView.as_view(), name='teacher-subjects-list'),
    path('<int:teacher_id>/availability/', TeacherAvailabilityListAPIView.as_view(), name='teacher-availability-list'),
]
# teachers/urls.py

from django.urls import path
from .views import TeacherProfileUpdateView

urlpatterns = [
    path('teacher-profile/', TeacherProfileUpdateView.as_view(), name='teacher-profile-update'),
]
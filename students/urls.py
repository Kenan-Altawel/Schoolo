from rest_framework.authtoken.views import obtain_auth_token 
from django.urls import path, include
from .views import *

urlpatterns = [
    # path('loginsuperuser/', obtain_auth_token, name='api_login'),
    path('pending-students/', PendingStudentList.as_view(), name='pending_student'), 
    path('<int:user_id>/student-status/', ApproveStudentAPIView.as_view(), name='student-accept-reject'),
    path('add-student/', ManagerAddStudentAPIView.as_view(), name='manager-add-student'),
    path('students-list/',StudentListAPIView.as_view(), name='section-students-list'),
]
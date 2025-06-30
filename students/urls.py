from rest_framework.authtoken.views import obtain_auth_token 
from django.urls import path, include
from .views import PendingStudentList,ApproveStudentAPIView

urlpatterns = [
    # path('loginsuperuser/', obtain_auth_token, name='api_login'),
    path('pending-students/', PendingStudentList.as_view(), name='pending_student'), 
    path('<int:user_id>/student-status/', ApproveStudentAPIView.as_view(), name='student-accept-reject'),

]
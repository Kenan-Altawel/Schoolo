from rest_framework.authtoken.views import obtain_auth_token 
from django.urls import path, include
from .views import *

urlpatterns = [
    path('student-login/', StudentloginView.as_view(), name='student_login'),
    path('superuser-login/', SuperuserLoginView.as_view(), name='superuser-login'),
    path('admin-login/', AdminLoginView.as_view(), name='admin_login'),
    path('adminsuperuser-login/', AdminSuperuserLoginView.as_view(), name='superuseradmin_login'),
    path('teacher-login/', TeacherLoginView.as_view(), name='teacher_login'),
    path('register-student/', StudentRegistrationView.as_view(), name='register_student'), 
    path('register-teacher/', TeacherRegistrationView.as_view(), name='teacher_register'),
    path('register-admin/', AdminRegistrationView.as_view(), name='admin_register'),
    path('send-otp/', OTPSendView.as_view(), name='send_otp'),
    path('verify-otp/', OTPVerifyView.as_view(), name='verify_otp'),
    path('set-password/', SetPasswordView.as_view(), name='set_password'),
    path('logout/', LogoutView.as_view(), name='logout'),

]
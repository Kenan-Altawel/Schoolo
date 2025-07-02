from rest_framework.authtoken.views import obtain_auth_token 
from django.urls import path, include
from .views import *

urlpatterns = [
    path('registration/', RegistrationSettingView.as_view(), name='registration'),


]
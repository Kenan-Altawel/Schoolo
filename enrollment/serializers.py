from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import RegistrationSetting

class GlobalRegistrationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationSetting
        fields = ['is_registration_open']
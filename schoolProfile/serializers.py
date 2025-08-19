from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import SchoolProfile
from enrollment.models import RegistrationSetting

class SchoolProfileSerializer(serializers.ModelSerializer):
    is_registration_open = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SchoolProfile
        fields = [
            'school_name',
            'school_phone',
            'school_logo',
            'email',
            'address',
            'school_type',
            'school_status',
            'is_registration_open',
        ]

    def get_is_registration_open(self, obj):
        setting, _ = RegistrationSetting.objects.get_or_create(pk=1)
        return setting.is_registration_open 
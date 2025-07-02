from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from .models import RegistrationSetting
from .serializers import GlobalRegistrationSettingSerializer
from accounts.permissions import *
class RegistrationSettingView(APIView):
    """
    واجهة برمجة تطبيقات للتحكم في حالة التسجيل العامة (مفتوح/مغلق).
    يمكن للمدراء فقط جلب وتحديث هذه الإعدادات.
    """
    permission_classes = [IsSuperuser] 
    def get(self, request, *args, **kwargs):
        """
        جلب حالة التسجيل الحالية.
        """
        setting, created = RegistrationSetting.objects.get_or_create(pk=1) 
        serializer = GlobalRegistrationSettingSerializer(setting)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """
        تحديث حالة التسجيل (فتح أو إغلاق التسجيل).
        """
        setting, created = RegistrationSetting.objects.get_or_create(pk=1)
        serializer = GlobalRegistrationSettingSerializer(setting, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """
        تحديث جزئي لحالة التسجيل (يمكن استخدامها لتغيير is_registration_open فقط).
        """
        setting, created = RegistrationSetting.objects.get_or_create(pk=1)
        serializer = GlobalRegistrationSettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


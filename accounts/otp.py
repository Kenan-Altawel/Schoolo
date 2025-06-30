
import random
from venv import logger
import requests
import json
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import OTP
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

def generate_otp():
    """Generates a 6-digit OTP as string."""
    return str(random.randint(100000, 999999))


def send_sms(phone_number,message):
    headers = {
        "Authorization": settings.TRACCAR_SMS_API_KEY,
        "Content-Type": "application/json",
    }
    
    payload = {
        "to": phone_number,
        "message": message
    }
    
    try:
        response = requests.post(
            settings.TRACCAR_SMS_URL,
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()  # يرفع استثناء إذا كان هناك خطأ HTTP
        return {"status": "success", "response": response.json()}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def send_otp_sms(phone , otp_code):
    """Generates and sends an OTP to the phone number. Returns the OTP if sent successfully."""
    message = f"كود التحقق الجديد الخاص بك هو: " + otp_code
    try:
        send_sms(phone, message)
        return Response(
            {"message": "تم إرسال كود تحقق جديد إلى هاتفك. الرجاء إدخال الكود لتأكيد حسابك."},
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        print(f"فشل إرسال رسالة SMS: {e}")
        return Response({"error": "فشل إرسال كود التحقق. الرجاء المحاولة لاحقًا."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def create_and_send_otp(user):
    OTP.objects.filter(user=user, is_verified=False).delete()
    otp_code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    otp_obj = OTP.objects.create(
        user=user,
        code=otp_code,
        expires_at=expires_at
    )

    try:
        sms_sent_successfully = send_otp_sms(user.phone_number, otp_code)

        if not sms_sent_successfully:
            otp_obj.delete()
            raise serializers.ValidationError(
                {"detail": _("فشل إرسال كود التحقق. الرجاء المحاولة لاحقًا.")}
            )
    except Exception as e:
        print(f"فشل إرسال رسالة SMS: {e}")
        otp_obj.delete() # حذف الـ OTP في حالة وجود خطأ
        raise serializers.ValidationError(
            {"detail": _("حدث خطأ أثناء إرسال كود التحقق. الرجاء المحاولة لاحقًا.")}
        )
    
    return {
        'phone_number': user.phone_number, 
        'message': _('تم إرسال رمز التحقق إلى رقم هاتفك.'),
    }

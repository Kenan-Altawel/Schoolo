from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import *
import logging
from rest_framework.exceptions import ValidationError 
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .permissions import *

logger = logging.getLogger(__name__)

class StudentRegistrationView(generics.CreateAPIView):
    
    serializer_class = StudentRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            registration_setting = RegistrationSetting.objects.get(pk=1)
            if not registration_setting.is_registration_open:
                return Response(
                    {"detail": _("التسجيل مغلق حالياً. الرجاء المحاولة في وقت لاحق.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except RegistrationSetting.DoesNotExist:
            logger.error("GlobalRegistrationSetting does not exist. Please create it in Django Admin or check AppConfig.")
            return Response(
                {"detail": _("حدث خطأ في النظام: إعدادات التسجيل غير متوفرة. الرجاء التواصل مع الإدارة.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        with transaction.atomic():
            try:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                user = serializer.validated_data
                student_status = user['student_status']
                response_data = {}
                response_data['phone_number'] = user['phone_number']
                
                if student_status == 'Existing':
                    response_data['message'] = _("تم تسجيل طلبك . قم بمراجعة الإدارة خلال 15 يوم لاستكمال الإجراءات.")
                elif student_status == 'New':
                    response_data['message'] = _("تم تسجيل طلبك . الرجاء القدوم إلى المدرسة لاستكمال إجراءات التسجيل.")
                
                serializer.save()
                return Response(response_data, status=status.HTTP_201_CREATED)

            except ValidationError as e: 
                logger.error(f"Validation error during student registration: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.exception("An unexpected error occurred during student registration.")
                return Response(
                    {'detail': _(f"حدث خطأ غير متوقع أثناء التسجيل: {e}")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR 
                )

class StudentloginView(TokenObtainPairView):
    """
    نقطة نهاية تسجيل الدخول المخصصة للطلاب فقط.
    تستخدم StudentTokenObtainPairSerializer للتحقق من الدور وتخصيص التوكن.
    """
    permission_classes = (AllowAny,)
    serializer_class = StudentloginSerializer


class SuperuserLoginView(TokenObtainPairView):
    """
    نقطة نهاية تسجيل الدخول المخصصة للمشرفين فقط.
    تستخدم SuperuserLoginSerializer للتحقق من الدور وتخصيص التوكن.
    """
    permission_classes = [AllowAny]
    serializer_class = SuperuserLoginSerializer

class TeacherRegistrationView(generics.CreateAPIView):
    
    serializer_class = TeacherRegistrationSerializer
    permission_classes = [IsAdminOrSuperuser]
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
                try:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

                except ValidationError as e: 
                    logger.error(f"Validation error during student registration: {e.detail}")
                    return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
                
class AdminRegistrationView(generics.CreateAPIView):

    
    serializer_class = AdminRegistrationSerializer
    permission_classes = [IsAdminOrSuperuser]
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
                try:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

                except ValidationError as e: 
                    logger.error(f"Validation error during student registration: {e.detail}")
                    return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

class SetPasswordView(APIView):
    """
    واجهة برمجة تطبيقات لتعيين كلمة مرور جديدة لحسابات المدراء والمعلمين.
    تتطلب رقم الهاتف وكلمة المرور الجديدة وتأكيدها.
    بعد التعيين بنجاح، تقوم بإنشاء وإرجاع توكنات JWT للمصادقة.
    """
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        """
        يتعامل مع طلبات POST لتعيين كلمة مرور المستخدم.
        """
        serializer = SetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # استدعاء دالة save() في السيريالايزر، والتي ستقوم بتعيين كلمة المرور
                # وإنشاء توكنات JWT وإرجاعها في الاستجابة.
                response_data = serializer.save()
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                # التعامل مع أي استثناءات غير متوقعة قد تحدث أثناء عملية الحفظ
                print(f"خطأ غير متوقع أثناء تعيين كلمة المرور: {e}")
                return Response(
                    {"detail": _("حدث خطأ داخلي أثناء معالجة طلبك. يرجى المحاولة لاحقًا.")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # إذا كانت البيانات غير صالحة، إرجاع أخطاء التحقق
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BaseLoginAPIView(APIView):
    """
    واجهة برمجة تطبيقات أساسية مشتركة لتسجيل الدخول.
    تستخدم سيريالايزر محدد بواسطة `serializer_class`.
    """
    serializer_class = None 

    def post(self, request, *args, **kwargs):
        """
        يتعامل مع طلبات POST لتسجيل الدخول باستخدام السيريالايزر المحدد.
        """
        if self.serializer_class is None:
            return Response(
                {"detail": _("خطأ في تكوين الخادم: لم يتم تحديد سيريالايزر.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                response_data = serializer.save()
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"خطأ غير متوقع أثناء معالجة طلب تسجيل الدخول: {e}")
                return Response(
                    {"detail": _("حدث خطأ داخلي أثناء معالجة طلبك. يرجى المحاولة لاحقًا.")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminLoginView(BaseLoginAPIView):
    """
    واجهة برمجة تطبيقات لتسجيل دخول المدراء.
    تستخدم AdminLoginSerializer.
    """
    serializer_class = AdminLoginSerializer
    permission_classes = [AllowAny]

class AdminSuperuserLoginView(TokenObtainPairView):
    """
    نقطة نهاية تسجيل الدخول للمسؤولين والمشرفين العامين.
    تتحقق من أن المستخدم إما مسؤول أو مشرف عام وتوفر التوكن ومعلومات الدور.
    """
    permission_classes = [AllowAny]
    serializer_class = AdminOrSuperuserLoginSerializer

class TeacherLoginView(BaseLoginAPIView):
    """
    واجهة برمجة تطبيقات لتسجيل دخول المعلمين.
    تستخدم TeacherLoginSerializer.
    """
    serializer_class = TeacherLoginSerializer
    permission_classes = [AllowAny]



class OTPSendView(APIView):
    """
    نقطة نهاية لإرسال رمز التحقق OTP إلى رقم هاتف المستخدم.
    """
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = OTPSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = serializer.save() 
        return Response(response_data, status=status.HTTP_200_OK)
    
class OTPVerifyView(APIView):
    """
    نقطة نهاية للتحقق من رمز التحقق OTP المدخل.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        response_data = serializer.save() 
        return Response(response_data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    واجهة برمجة تطبيقات لتسجيل خروج المستخدم.
    تتطلب توكن التحديث (refresh token) لوضعه في القائمة السوداء.
    """
    permission_classes = (IsAuthenticated,) # تأكد أن المستخدم مسجل الدخول قبل محاولة تسجيل الخروج

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT) # 204 No Content يدل على نجاح العملية بدون إرجاع محتوى




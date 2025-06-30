import datetime
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import Teacher
from admins.models import Admin
from .models import User , OTP
from classes.models import Class
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.contrib.auth.models import Group
import logging 
from datetime import timedelta
from django.db.utils import IntegrityError 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .otp import create_and_send_otp , send_otp_sms , generate_otp
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken 
from .tokens import get_tokens_for_user
User = get_user_model() # جلب موديل المستخدم المخصص


logger = logging.getLogger(__name__)
    
class StudentRegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}) 
    first_name = serializers.CharField(max_length=100, required=True, label="الاسم الأول")
    last_name = serializers.CharField(max_length=100, required=True, label="اسم العائلة")
    father_name = serializers.CharField(max_length=100, allow_blank=True, required=False, label="اسم الأب")
    gender = serializers.ChoiceField(choices=Student.GENDER_CHOICES, required=True, label="الجنس")
    address = serializers.CharField(max_length=255, allow_blank=True, required=False, label="العنوان")
    parent_phone = serializers.CharField(max_length=20, allow_blank=True, required=False, label="رقم هاتف ولي الأمر")
    student_status = serializers.ChoiceField(choices=Student.STUDENT_STATUS_CHOICES, required=False, default='New', label="حالة الطالب")
    student_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), required=True,allow_null=False,label=_("الصف الدراسي"))
    date_of_birth = serializers.DateField(required=False, allow_null=True, label="تاريخ الميلاد")
    image = serializers.ImageField(required=False, allow_null=True, label="صورة الطالب")


    class Meta:
        model = User
        fields = [
            'phone_number', 'password', 'password2',
            'first_name', 'last_name', 'father_name', 'gender', 'address',
            'parent_phone',  'student_status', 'student_class', 'date_of_birth', 'image'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
           
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": _("كلمتا المرور غير متطابقتين.")})
        
        if User.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError({"phone_number": _("رقم الهاتف هذا مسجل بالفعل.")})
            
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            try:
                user_data = {
                    'phone_number': validated_data.pop('phone_number'),
                    'password': validated_data.pop('password'),
                    'first_name': validated_data.pop('first_name'),
                    'last_name': validated_data.pop('last_name'),
                    
                }
                validated_data.pop('password2') 

               
                student_data = {
                    'father_name': validated_data.pop('father_name', ''), 
                    'gender': validated_data.pop('gender'),
                    'address': validated_data.pop('address', ''),
                    'parent_phone': validated_data.pop('parent_phone', ''),
                    'student_status': validated_data.pop('student_status', 'New'),
                    'student_class':validated_data.pop('student_class',''),
                    'date_of_birth': validated_data.pop('date_of_birth', None),
                    'image': validated_data.pop('image', None),
                }

                
                user = User.objects.create_student_user(**user_data) 
                student = Student.objects.create(user=user, **student_data)

                return user 

            except IntegrityError as e:
                logger.error(f"Database Integrity Error during user/student creation: {e}")
                raise serializers.ValidationError(_("حدث خطأ في قاعدة البيانات. قد تكون بعض البيانات مكررة. الرجاء التحقق من البيانات والمحاولة مرة أخرى."))
            except Exception as e:
                logger.exception("An unexpected error occurred during user/student registration.") 
                raise serializers.ValidationError(_("حدث خطأ غير متوقع أثناء التسجيل. الرجاء المحاولة لاحقاً.: "+ str(e)))

class StudentloginSerializer(TokenObtainPairSerializer):

    username_field = 'phone_number' # استخدام رقم الهاتف كاسم مستخدم

    def validate(self, attrs):
        data = super().validate(attrs) 
        
        user = self.user 

        if not user.is_active:
            raise serializers.ValidationError(
                {'detail': _('الحساب غير نشط. يرجى الاتصال بالإدارة لتفعيله.')}
            )
        
        if not user.is_student():
            raise serializers.ValidationError(
                {'detail': _('بيانات الاعتماد غير صالحة لدخول الطلاب. يرجى استخدام بوابة الدخول الصحيحة.')}
            )
        if not user.is_phone_verified:
            raise serializers.ValidationError(
                {
                    'detail': _('يرجى تأكيد رقم هاتفك لإكمال عملية تسجيل الدخول.'),
                }
            )

        if hasattr(user, 'student'): 
            if user.student.register_status not in ['Accepted']:
                raise serializers.ValidationError(
                    {'detail': _('حساب الطالب هذا غير مقبول أو مسجل بعد. يرجى مراجعة إدارة المدرسة.')}
                )
        else:
            raise serializers.ValidationError(
                {'detail': _('المستخدم في مجموعة الطلاب ولكن لا يوجد ملف طالب مرتبط به. يرجى الاتصال بالدعم.')}
            )

        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        user_groups = [group.name for group in user.groups.all()]
        data['groups'] = user_groups 
        data['role'] = 'student' 

        return data

class TeacherRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100, required=True, label="الاسم الأول")
    last_name = serializers.CharField(max_length=100, required=True, label="اسم العائلة")
    specialization= serializers.CharField(max_length=100, required=True)
    class Meta:
        model = User
        fields = [
            'phone_number',
            'first_name', 'last_name', 'specialization'
        ]
    def validate(self, attrs):
        if User.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError({"phone_number": _("رقم الهاتف هذا مسجل بالفعل.")})
            
        return attrs

    def create(self, validated_data):
        user_data = {
            'phone_number': validated_data.pop('phone_number'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
        }
        teacher_data = {
            'specialization': validated_data.pop('specialization'),
        }

        user = User.objects.create_teacher_user(**user_data)
        
        teacher = Teacher.objects.create(user=user, **teacher_data)
        return user

class AdminRegistrationSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(max_length=100, required=True, label="الاسم الأول")
    last_name = serializers.CharField(max_length=100, required=True, label="اسم العائلة")
    department= serializers.CharField(max_length=100, required=True)
    class Meta:
        model = User
        fields = [
            'phone_number',
            'first_name', 'last_name', 'department'
        ]
    def validate(self, attrs):
        if User.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError({"phone_number": _("رقم الهاتف هذا مسجل بالفعل.")})
            
        return attrs

    def create(self, validated_data):
        user_data = {
            'phone_number': validated_data.pop('phone_number'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
        }
        admin_data = {
            'department': validated_data.pop('department'),
        }

        user = User.objects.create_admin_user(**user_data)
        
        admin = Admin.objects.create(user=user, **admin_data)
        return user

class SetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15, required=True, label=_("رقم الهاتف"))
    new_password = serializers.CharField(max_length=128, min_length=8, write_only=True, required=True, label=_("كلمة المرور الجديدة"))
    confirm_password = serializers.CharField(max_length=128, min_length=8, write_only=True, required=True, label=_("تأكيد كلمة المرور الجديدة"))

    def validate(self, data):
        phone_number = data.get('phone_number')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError(_("كلمتا المرور غير متطابقتين."))

        try:
            user = User.objects.get(phone_number=phone_number)
            self.user = user 
        except User.DoesNotExist:
            raise serializers.ValidationError(_("رقم الهاتف غير مسجل."))

        if not (user.groups.filter(name='Manager').exists() or user.groups.filter(name='Teacher').exists()):
            raise serializers.ValidationError(_("هذا الحساب ليس حساب مدير أو معلم، ولا يمكن تعيين كلمة المرور له بهذه الطريقة."))
        
        if not user.is_phone_verified:
            raise serializers.ValidationError(_("رقم الهاتف غير مؤكد بعد. يرجى تأكيد رقم هاتفك أولاً."))

        return data

    def save(self, **kwargs):
        """
        يقوم بتعيين كلمة المرور الجديدة للمستخدم وإنشاء توكنات Simple JWT.
        """
        user = self.user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return {
            'message': _('تم تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.'),
            'access_token': access_token,  
            'refresh_token': str(refresh), 
            'user_id': user.id,
            'phone_number': user.phone_number,
            'user_role': 'admin' if user.groups.filter(name='Manager').exists() else ('teacher' if user.groups.filter(name='Teacher').exists() else 'user')
        }

class SuperuserLoginSerializer(TokenObtainPairSerializer):
    username_field = 'phone_number'

    def validate(self, attrs):
       
        data = super().validate(attrs)
        
        user = self.user 

        if not user.is_active:
            raise serializers.ValidationError(
                {'detail': _('الحساب غير نشط. يرجى الاتصال بالإدارة لتفعيله.')}
            )
        
        if not user.is_superuser:
            raise serializers.ValidationError(
                {'detail': _('ليس لديك صلاحيات مشرف (superuser). يرجى استخدام بوابة الدخول الصحيحة.')}
            )
        
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['role'] = 'superuser' 

        return data

class BaseLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15, required=True, label=_("رقم الهاتف"))
    password = serializers.CharField(write_only=True, required=True, label=_("كلمة المرور"))
    user_role = serializers.CharField(read_only=True) 

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')


        if not phone_number or not password:
            raise serializers.ValidationError(_("يجب توفير رقم الهاتف وكلمة المرور."))
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("رقم الهاتف غير مسجل."))

        if not user.is_active:
            raise serializers.ValidationError(_("هذا الحساب غير نشط."))
        
        if not user.is_phone_verified:
            raise serializers.ValidationError(_("رقم الهاتف غير مؤكد بعد. يرجى تأكيد رقم هاتفك أولاً."))

        
        if not user.check_password(password):
            raise serializers.ValidationError(_("كلمة المرور غير صحيحة."))


        
        self.user = user
        return data

    def save(self, **kwargs):
        """
        تقوم بتسجيل الدخول الفعلي وإنشاء توكنات JWT.
        """
        user = self.user
        tokens = get_tokens_for_user(user)

        user_role = '' 
        if user.groups.filter(name='Manager').exists():
            user_role = 'admin'
        elif user.groups.filter(name='Teacher').exists():
            user_role = 'teacher'

        return {
            'message': _('تم تسجيل الدخول بنجاح.'),
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'user_id': user.id,
            'phone_number': user.phone_number,
            'user_role': user_role,
        }

class AdminLoginSerializer(BaseLoginSerializer):
    """
    سيريالايزر لتسجيل دخول المدراء فقط.
    """
    def validate(self, data):
        data = super().validate(data)
        
        user = self.user 
        if not user.groups.filter(name='Manager').exists():
            raise serializers.ValidationError(_("هذا الحساب ليس حساب مدير."))
            
        return data

    def save(self, **kwargs):
        response_data = super().save(**kwargs)
        response_data['user_role'] = 'admin'
        return response_data

class TeacherLoginSerializer(BaseLoginSerializer):
    """
    سيريالايزر لتسجيل دخول المعلمين فقط.
    """
    def validate(self, data):
        data = super().validate(data)
        
        user = self.user 
        if not user.groups.filter(name='Teacher').exists():
            raise serializers.ValidationError(_("هذا الحساب ليس حساب معلم."))
            
        return data

    def save(self, **kwargs):
        response_data = super().save(**kwargs)
        response_data['user_role'] = 'teacher'
        return response_data

class OTPSendSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15, required=True, label=_("رقم الهاتف"))
    password = serializers.CharField(write_only=True, required=False, label=_("كلمة المرور")) 

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        try:
            user = User.objects.get(phone_number=phone_number)
            self.user = user
        except User.DoesNotExist:
            raise serializers.ValidationError(_("رقم الهاتف غير مسجل."))

        if password:
            if not user.check_password(password):
                raise serializers.ValidationError(_("كلمة المرور غير صحيحة."))

            if not user.groups.filter(name='Student').exists():
                raise serializers.ValidationError(_("هذا الحساب ليس حساب طالب."))
            
            self.user_role = 'student'

        else:
            
            if user.groups.filter(name='Manager').exists():
                self.user_role = 'admin'
            elif user.groups.filter(name='Teacher').exists():
                self.user_role = 'teacher'
            else:
                raise serializers.ValidationError(_("لا تسطيع التسجيل في المدرسة بهذه الطريقة."))

        return data

    def create(self, validated_data):
        user = self.user
        response_data = create_and_send_otp(user)
        response_data['user_role'] = self.user_role
        return response_data

class OTPVerifySerializer(serializers.Serializer):


    phone_number = serializers.CharField(max_length=15, required=True, label=_("رقم الهاتف"))
    otp_code = serializers.CharField(max_length=6, required=True, label=_("رمز التحقق"))

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        otp_code = attrs.get('otp_code')

        try:
            user = User.objects.get(phone_number=phone_number)
            self.user = user # حفظ المستخدم للوصول إليه في دالة create
        except User.DoesNotExist:
            raise serializers.ValidationError(_("رقم الهاتف غير مسجل."))

        if user.is_phone_verified: 
            raise serializers.ValidationError(_("تم تأكيد رقم الهاتف لهذا المستخدم بالفعل."))

        try:
            otp_obj = OTP.objects.filter(
                user=user, 
                code=otp_code, 
                is_verified=False,
                expires_at__gt=timezone.now() 
            ).latest('created_at') 
            self.otp_obj = otp_obj 
        except OTP.DoesNotExist:
            raise serializers.ValidationError(_("رمز التحقق غير صحيح أو انتهت صلاحيته."))

        return attrs

    def create(self, validated_data):
        with transaction.atomic(): 
            otp_obj = self.otp_obj
            user = self.user
            
            user.is_active=True
            otp_obj.is_verified = True
            otp_obj.save()

            user.is_phone_verified = True
            user.save()

            return {'message': _('تم تأكيد رقم الهاتف بنجاح. يمكنك الآن تسجيل الدخول.')}
        


import datetime
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import Teacher
from admins.models import Admin
from .models import User , OTP
from classes.models import Class
from django.utils.translation import gettext_lazy as _
from django.db import transaction
import logging 
from rest_framework.exceptions import AuthenticationFailed
from django.db.utils import IntegrityError 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .otp import create_and_send_otp 
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken 
from .tokens import get_tokens_for_user
User = get_user_model()
from subject.serializers import *
from subject.models import  TeacherSubject


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
                    'phone_verified': user.is_phone_verified,
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
        data['role'] = 'student' 
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['phone_number'] = str(user.phone_number) 

        return data

class TeacherRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100, required=True, label="الاسم الأول")
    last_name = serializers.CharField(max_length=100, required=True, label="اسم العائلة")
    specialization= serializers.CharField(max_length=100, required=True)
    subjects_to_teach = TeacherSubjectAssignmentSerializer(
        many=True,
        required=False, 
        label=_("المواد المراد تدريسها")
    )

    class Meta:
        model = User
        fields = [
            'phone_number',
            'first_name', 'last_name', 'specialization', 'subjects_to_teach',
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
        subjects_to_teach_data = validated_data.pop('subjects_to_teach', [])
        user = User.objects.create_teacher_user(**user_data)
        
        try:
            teacher = user.teacher_profile
        except Teacher.DoesNotExist:
            teacher = Teacher.objects.create(user=user, **teacher_data)

        for subject_assignment in subjects_to_teach_data:
            subject_id = subject_assignment['subject_id']
            weekly_hours = subject_assignment['weekly_hours']
            

            TeacherSubject.objects.create(
                teacher=teacher, 
                subject=subject_id, 
                weekly_hours=weekly_hours
            )
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
            'user_role': 'admin' if user.groups.filter(name='Manager').exists() else (
            'teacher' if user.groups.filter(name='Teacher').exists() else (
            'student' if user.groups.filter(name='Student').exists() else 'user'
        )
    )}

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
class AdminOrSuperuserLoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        if user.is_superuser:
            token['role'] = 'superuser'
        elif user.is_staff:
            token['role'] = 'admin'
        else:
            return "you can not access this" 
        
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['phone_number'] = str(user.phone_number) 

        return token

    def validate(self, attrs):
        data = super().validate(attrs) 

        user = self.user 

        if not user.is_staff and not user.is_superuser:
            raise AuthenticationFailed(_("غير مصرح: هذا الحساب ليس حساب مسؤول أو مشرف عام."))

        if user.is_superuser:
            data['role'] = 'superuser'
        elif user.is_staff:
            data['role'] = 'admin'

        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['phone_number'] = str(user.phone_number) 

        return data
    
class TeacherLoginSerializer(BaseLoginSerializer):
    """
    سيريالايزر لتسجيل دخول المعلمين فقط.
    """
    def validate(self, data):
        data = super().validate(data)
        
        user = self.user 
        if not user.groups.filter(name='Teacher').exists():
            raise serializers.ValidationError(_("هذا الحساب ليس حساب معلم."))
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['phone_number'] = str(user.phone_number) 

        return data

    def save(self, **kwargs):
        data = super().save(**kwargs)
        data['user_role'] = 'teacher'
        
        return data

class OTPSendSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15, required=True, label=_("رقم الهاتف"))
    password = serializers.CharField(write_only=True, required=False, label=_("كلمة المرور")) 

    def validate(self, data):
        phone_number = data.get('phone_number')

        try:
            user = User.objects.get(phone_number=phone_number)
            self.user = user
        except User.DoesNotExist:
            raise serializers.ValidationError(_("رقم الهاتف غير مسجل."))

        else:
            
            if user.groups.filter(name='Manager').exists():
                self.user_role = 'admin'
                print('Manager')
            elif user.groups.filter(name='Teacher').exists():
                self.user_role = 'teacher'
                print('Teacher')
            elif user.groups.filter(name='Student').exists():
                self.user_role = 'student'            
            elif user.is_superuser:
                self.user_role = 'manager'
            else :
                raise serializers.ValidationError(_("انت غير مسجل في المدرسة "))

        return data

    def create(self, validated_data):
        user = self.user
        response_data = create_and_send_otp(user)
        response_data['user_role'] = self.user_role
        return response_data

class OTPVerifySerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=15, required=True, label=_("رقم الهاتف"))
    otp_code = serializers.CharField(max_length=6, required=True, label=_("رمز التحقق"))
    purpose = serializers.ChoiceField(
        choices=[('phone_verification', _('تأكيد رقم الهاتف')), ('password_reset', _('إعادة تعيين كلمة المرور'))],
        required=True,
        label=_("الغرض من التحقق")
    )
    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        otp_code = attrs.get('otp_code')
        purpose = attrs.get('purpose')
        try:
            user = User.objects.get(phone_number=phone_number)
            self.user = user 
        except User.DoesNotExist:
            raise serializers.ValidationError(_("رقم الهاتف غير مسجل."))

        if purpose == 'phone_verification':
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
            purpose = validated_data.get('purpose')
            
            user.is_active=True
            otp_obj.is_verified = True
            otp_obj.save()

            user.is_phone_verified = True
            user.save()
            if purpose == 'phone_verification':
                user.is_phone_verified = True
                user.is_active = True
                user.save()
                return {'message': _('تم تأكيد رقم الهاتف بنجاح. يمكنك الآن تسجيل الدخول.')}

            elif purpose == 'password_reset':
                return {'message': _('تم التحقق من رمز التحقق بنجاح. يمكنك الآن تعيين كلمة مرور جديدة.'), 'user_id': user.id}

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True) # يتوقع توكن التحديث

    default_error_messages = {
        'bad_token': _('توكن التحديث غير صالح أو منتهي الصلاحية.')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        """
        يقوم بوضع توكن التحديث في القائمة السوداء.
        """
        try:
            refresh_token = RefreshToken(self.token)
            refresh_token.blacklist()
        except Exception as e:
            
            raise AuthenticationFailed(self.error_messages['bad_token'], 'bad_token')
        
        return {'message': _('تم تسجيل الخروج بنجاح.')}

class StudentSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='section.name', read_only=True)
    class_name = serializers.CharField(source='student_class.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'enrollment_number', 'father_name', 'gender', 'address',
            'parent_phone', 'student_status', 'register_status',
            'date_of_birth', 'image',  'section','section_name', 'student_class','class_name',
        ]
from teachers.serializers import TeacherAvailabilitySerializer
class TeacherSerializer(serializers.ModelSerializer):
    availability = TeacherAvailabilitySerializer(many=True, read_only=True)
    class Meta:
        model = Teacher
        fields = [
            'address', 'specialization','availability',
        ]

# سيريالايزر لبيانات المدير
class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = [
            'department',
        ]

# السيريالايزر الرئيسي للمستخدم، والذي يضم السيريالايزرات الأخرى
class UserProfileSerializer(serializers.ModelSerializer):
    role_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'phone_number', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser',
            'is_phone_verified', 'last_login', 'role_info',
            'id', 'get_full_name' 
        ]
        read_only_fields = ['id', 'phone_number', 'get_full_name']

    def get_role_info(self, obj):
        if obj.is_student():
            try:
                student_profile = obj.student
                return StudentSerializer(student_profile).data
            except Student.DoesNotExist:
                return None
        
        elif obj.is_teacher():
            try:
                teacher_profile = obj.teacher_profile
                return TeacherSerializer(teacher_profile).data
            except Teacher.DoesNotExist:
                return None

        elif obj.is_admin():
            try:
                admin_profile = obj.admin_profile
                return AdminSerializer(admin_profile).data
            except Admin.DoesNotExist:
                return None
        
        return None
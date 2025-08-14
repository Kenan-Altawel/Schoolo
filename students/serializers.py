from rest_framework import serializers
from .models import Student 
from classes.models import Class, Section 
from django.contrib.auth.models import Group
from accounts.models import User
from django.contrib.auth import get_user_model
from django.db import transaction
import logging 
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)

class ClassListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'name']

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'name', 'capacity'] 
#سيريالايزر لعرض الطلاب المسجلين لقبولهم
class PendingStudentApplicationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_is_active = serializers.BooleanField(source='user.is_active', read_only=True) 
    id_class_details = ClassListSerializer(source='student_class', read_only=True) 
    section_details = SectionSerializer(source='section', read_only=True) 

    class Meta:
        model = Student
        fields = [ 
            'user_id',
            'phone_number', 
            'first_name', 
            'last_name',
            'father_name', 
            'gender', 
            'address', 
            'parent_phone',
            'student_status', 
            'date_of_birth', 
            'image', 
            'user_is_active', 
            'student_class',
            'id_class_details', 
            'section', 
            'section_details',
        ]
        read_only_fields = fields 


#سيريالايزر لقبول الطلاب 
class StudentAcceptanceSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    student_class_details = ClassListSerializer(source='student_class', read_only=True)
    section_details = SectionSerializer(source='section', read_only=True)
    user_is_active = serializers.BooleanField(source='user.is_active')

    class Meta:
        model = Student
        fields = [
            'user_id', 'phone_number', 'first_name', 'last_name',
            'father_name', 'gender', 'address', 'parent_phone', 
            'date_of_birth', 'image', 'student_class', 'student_class_details',
            'register_status', 'section', 'section_details', 'user_is_active','student_status'
        ]
        read_only_fields = [
            'user_id', 'phone_number', 'first_name', 'last_name',
            'father_name', 'gender', 'address', 'parent_phone',
            'date_of_birth', 'image', 'student_class', 'student_class_details','student_status'
        ]

    def validate(self, data):
        student = self.instance
        new_status = data.get('register_status')
        new_section = data.get('section')

        if new_status == 'Accepted':
            data['user_is_active'] = True
            if not new_section:
                raise serializers.ValidationError(
                    {"section": "يجب تحديد الشعبة عند قبول الطالب"}
                )
            
            if new_section.class_obj != student.student_class:
                raise serializers.ValidationError(
                    {"section": "الشعبة المحددة لا تنتمي للصف الذي اختاره الطالب"}
                )
            
        elif new_status == 'Rejected':
            data['section'] = None
            data['user_is_active'] = False

        return data

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user_is_active_value = validated_data.pop('user_is_active', None)
        
        # تحديث حالة الطالب
        instance.register_status = validated_data.get('register_status', instance.register_status)
        instance.section = validated_data.get('section', instance.section)
        instance.save()

        # تحديث حالة المستخدم
        if user_is_active_value is not None: 
            instance.user.is_active = user_is_active_value 
            instance.user.save()

        return instance
    

#اضافة طالب من قبل المدير
User = get_user_model()

class ManagerStudentCreationSerializer(serializers.ModelSerializer):
    # الحقول المتعلقة بموديل User
    phone_number = serializers.CharField(max_length=10, write_only=True)
    first_name = serializers.CharField(max_length=150, required=True, write_only=True)
    last_name = serializers.CharField(max_length=150, required=True, write_only=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    # حقول Student مع التسميات العربية
    father_name = serializers.CharField(max_length=100, allow_blank=True, required=False, label=_("اسم الأب"))
    gender = serializers.ChoiceField(choices=Student.GENDER_CHOICES, required=True, label=_("الجنس"))
    address = serializers.CharField(max_length=255, allow_blank=True, required=False, label=_("العنوان"))
    parent_phone = serializers.CharField(max_length=20, allow_blank=True, required=False, label=_("رقم هاتف ولي الأمر"))
    student_status = serializers.ChoiceField(choices=Student.STUDENT_STATUS_CHOICES, required=False, default='New', label=_("حالة الطالب"))
    student_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), required=True, allow_null=False, label=_("الصف الدراسي"))
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all(), required=True, allow_null=False, label=_("الشعبة"))
    date_of_birth = serializers.DateField(required=False, allow_null=True, label=_("تاريخ الميلاد"))
    image = serializers.ImageField(required=False, allow_null=True, label=_("صورة الطالب"))

    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'phone_number', 'password', 'first_name', 'last_name',
            'father_name', 'gender', 'address', 'parent_phone',
            'student_class', 'section', 'date_of_birth', 'image','student_status',
            'user_id', 'user_phone_number', 'user_first_name', 'user_last_name',
        ]
        
    def validate(self, data):
        # التحقق من أن رقم الهاتف غير مستخدم مسبقاً
        phone_number = data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError(
                {"phone_number": "رقم الهاتف هذا مسجل بالفعل."}
            )

        # التحقق من أن الشعبة تنتمي إلى الصف
        section = data.get('section')
        student_class = data.get('student_class')
        if section and student_class and section.class_obj != student_class:
            raise serializers.ValidationError(
                {"section": "الشعبة المحددة لا تنتمي للمرحلة الدراسية المحددة."}
            )

        # التحقق من سعة الشعبة
        if section and section.students.count() >= section.capacity:
            raise serializers.ValidationError(
                {"section": "الشعبة المحددة وصلت إلى سعتها القصوى."}
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        try:
        # فصل بيانات المستخدم عن بيانات الطالب
            print(validated_data)
            
            user_data = {
                'phone_number': validated_data.pop('phone_number'),
                'password': validated_data.pop('password'),
                'first_name': validated_data.pop('first_name'),
                'last_name': validated_data.pop('last_name'),
                'is_active': True,
                'is_phone_verified':False
            }
            try:
        # إنشاء كائن المستخدم أولاً
                user = User.objects.create_student_user(**user_data)
            except Exception as e:
                logger.exception("An unexpected error occurred during user creation.")
                raise serializers.ValidationError(_(f"حدث خطأ غير متوقع أثناء إنشاء المستخدم. الرجاء المحاولة لاحقاً. الخطأ: {e}"))

            # إضافة كائن المستخدم إلى validated_data قبل إنشاء الطالب
            validated_data['user'] = user
            validated_data['register_status'] = 'Accepted'
            print(validated_data)

            try:
                # إنشاء كائن الطالب باستخدام باقي البيانات
                student = Student.objects.create(**validated_data)
            except Exception as e:
                logger.exception("An unexpected error occurred during student creation.")
                raise serializers.ValidationError(_(f"حدث خطأ غير متوقع أثناء إنشاء الطالب. الرجاء المحاولة لاحقاً. الخطأ: {e}"))

            # إرجاع كائن student لتمكين CreateAPIView من بناء الاستجابة
            return validated_data
        except Exception as e:
            logger.exception("An unexpected error occurred during user/student creation.") 
            raise serializers.ValidationError(_(str(e)  +"حدث خطأ غير متوقع أثناء الإضافة. الرجاء المحاولة لاحقاً."))

#عرض الطلاب   
class StudentListSerializer(serializers.ModelSerializer):
    
    user_data = serializers.SerializerMethodField()
    
    student_class = serializers.StringRelatedField(source='student_class.name')
    section = serializers.StringRelatedField(source='section.name')

    class Meta:
        model = Student
        fields = [
            'user_data',
            'father_name', 'gender', 'address', 'parent_phone',
            'student_class', 'section', 'date_of_birth', 'image',
            'student_status', 'register_status',
        ]

    def get_user_data(self, obj):
        user = obj.user
        if user:
            return {
                "id": user.id,
                "phone_number": user.phone_number,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        return None

class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['address',  'image']


class ManagerStudentUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    is_active = serializers.BooleanField(source='user.is_active', required=False)
    phone_number = serializers.CharField(source='user.phone_number', required=False)
    
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'is_active', 'phone_number',
            'father_name', 'gender', 'date_of_birth', 'address',
            'parent_phone', 'image', 'student_class', 'section',
            'student_status'
        ]

    def validate(self, data):
        section = data.get('section', self.instance.section)
        student_class = data.get('student_class', self.instance.student_class)

        if section and student_class and section.class_obj != student_class:
            raise serializers.ValidationError(
                {"section": "الشعبة المحددة لا تنتمي للمرحلة الدراسية المحددة."}
            )
        
        if section and section != self.instance.section:
            if section.students.count() >= section.capacity:
                raise serializers.ValidationError(
                    {"section": "الشعبة المحددة وصلت إلى سعتها القصوى."}
                )
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        return super().update(instance, validated_data)

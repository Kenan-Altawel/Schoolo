from rest_framework import serializers
from .models import Student 
from classes.models import Class, Section 
from django.contrib.auth.models import Group
from accounts.models import User


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
    


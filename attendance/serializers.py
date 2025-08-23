from rest_framework import serializers
from .models import Attendance
from students.models import Student
class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    recorded_by_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'date', 'status', 
            'status_display', 'recorded_by', 'recorded_by_name', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'student_name', 'recorded_by_name', 'status_display']

    def get_student_name(self, obj):
        # التحقق من وجود الطالب قبل محاولة الوصول إلى اسمه
        if isinstance(obj, Attendance):
            return obj.student.user.get_full_name()
        elif isinstance(obj, dict):
            # إذا كان قاموسًا، ابحث عن المفتاح 'student'
            student_id = obj.get('student')
            if student_id:
                try:
                    student_obj = Student.objects.get(pk=student_id)
                    return student_obj.user.get_full_name()
                except Student.DoesNotExist:
                    return None
        return None

    def get_recorded_by_name(self, obj):
        # التحقق من وجود المستخدم الذي سجل الحضور
        if obj.recorded_by:
            return obj.recorded_by.get_full_name()
        return None
    
    def get_status_display(self, obj):
        # استخدام دالة get_status_display() المضمنة في Django
        return obj.get_status_display()
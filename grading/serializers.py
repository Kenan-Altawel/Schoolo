# exams/serializers.py
from rest_framework import serializers
from .models import Exam
from subject.models import Subject 
from academic.models import AcademicYear, AcademicTerm 
from classes.models import Class, Section 
from classes.serializers import ClassSerializer, SectionSerializer
from academic.serializers import AcademicYearSerializer, AcademicTermSerializer

class ExamSerializer(serializers.ModelSerializer):
    subject_name = serializers.StringRelatedField(source='subject')
    academic_year_name = serializers.StringRelatedField(source='academic_year')
    academic_term_name = serializers.StringRelatedField(source='academic_term')
    teacher_name = serializers.SerializerMethodField()
    target_class_name = serializers.StringRelatedField(source='target_class')
    target_section_name = serializers.StringRelatedField(source='target_section')
    stream_type_display = serializers.CharField(source='get_stream_type_display', read_only=True)

    class Meta:
        model = Exam
        fields = [
            'id', 'subject', 'subject_name', 'academic_year', 'academic_year_name', 
            'academic_term', 'academic_term_name', 'exam_type', 'exam_date', 
            'total_marks', 'teacher', 'teacher_name', 'target_class', 
            'target_class_name', 'target_section', 'target_section_name', 
            'is_conducted', 'stream_type', 'stream_type_display',
        ]
        read_only_fields = ['is_conducted','stream_type_display']
        
    def get_teacher_name(self, obj):
        if obj.teacher:
            return obj.teacher.user.get_full_name()
        return None

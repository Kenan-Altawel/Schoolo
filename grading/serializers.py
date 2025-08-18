# exams/serializers.py
from rest_framework import serializers
from .models import *
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


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    exam_subject_name = serializers.CharField(source='exam.subject.name', read_only=True)
    exam_type = serializers.CharField(source='exam.get_exam_type_display', read_only=True)
    exam_total_marks = serializers.DecimalField(source='exam.total_marks', max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_name', 'exam', 'exam_subject_name',
            'exam_type', 'exam_total_marks', 'score', 'graded_at'
        ]
        read_only_fields = ['id', 'student_name', 'exam_subject_name', 'exam_type', 'exam_total_marks', 'graded_at']

         
        def validate(self, data):
            """
            يتحقق من أن الدرجة المحرزة لا تتجاوز الدرجة الكلية للامتحان.
            """
            exam = data.get('exam')
            score = data.get('score')
            
            if score is not None and exam is not None:
                if score > exam.total_marks:
                    raise serializers.ValidationError({
                        "score": "درجة الطالب لا يمكن أن تكون أكبر من الدرجة الكلية للاختبار."
                    })
                if score < 0:
                    raise serializers.ValidationError({
                        "score": "درجة الطالب لا يمكن أن تكون سالبة."
                    })
            
            return data

class BulkGradeItemSerializer(serializers.Serializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    score = serializers.DecimalField(max_digits=5, decimal_places=2)

class BulkGradeSerializer(serializers.Serializer):
    grades = serializers.ListField(
        child=BulkGradeItemSerializer()
    )

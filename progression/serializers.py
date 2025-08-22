# progression/serializers.py
from rest_framework import serializers
from .models import StudentProgression, StudentProgressionIssue
from students.models import Student
from classes.models import Class, Section
from academic.models import AcademicYear

class StudentProgressionIssueSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student_progression.student.user.get_full_name', read_only=True)
    student_id = serializers.IntegerField(source='student_progression.student.id', read_only=True)
    student_class_name = serializers.CharField(source='student_progression.student.student_class.name', read_only=True)
    student_section_name = serializers.CharField(source='student_progression.student.section.name', read_only=True)
    academic_year_name = serializers.CharField(source='student_progression.academic_year.name', read_only=True)

    class Meta:
        model = StudentProgressionIssue
        fields = [
            'id', 'issue_type', 'get_issue_type_display', 'description', 
            'is_resolved', 'resolved_at', 'student_name', 'student_id',
            'student_class_name', 'student_section_name', 'academic_year_name'
        ]

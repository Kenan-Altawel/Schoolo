# exams/serializers.py
from rest_framework import serializers
from .models import *
from subject.models import Subject 
from academic.models import AcademicYear, AcademicTerm 
from classes.models import Class, Section 
from classes.serializers import ClassSerializer, SectionSerializer
from academic.serializers import AcademicYearSerializer, AcademicTermSerializer
from django.utils.translation import gettext_lazy as _

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
        read_only_fields = ['is_conducted','stream_type_display','academic_year','academic_term']
        
    def get_teacher_name(self, obj):
        if obj.teacher:
            return obj.teacher.user.get_full_name()
        return None
    
    def validate(self, data):
        teacher = data.get('teacher')
        subject = data.get('subject')

        
        if teacher and subject:
            from subject.models import TeacherSubject 
            if not TeacherSubject.objects.filter(teacher=teacher, subject=subject).exists():
                raise serializers.ValidationError({
                    "teacher": _("المعلم المحدد لا يدرس هذه المادة.")
                })
        return data   
    
   
                
    # def validate(self, data):
    #     teacher = data.get('teacher')
    #     target_class = data.get('target_class')
    #     target_section = data.get('target_section')
    #     stream_type = data.get('stream_type')
    #     subject = data.get('subject')

    #     # التحقق من الشروط التي طلبتها فقط إذا كان المعلم والصف والمادة محددين
    #     if teacher and target_class and subject:
    #         # الشرط الأول: امتحان لصف كامل
    #         if not target_section and not stream_type:
    #             # حساب عدد الشعب في الصف
    #             all_sections_count = Section.objects.filter(class_obj=target_class).count()
                
    #             # حساب عدد الشعب التي يدرس فيها المعلم المادة
    #             taught_sections_count = teacher.teaching_subjects.filter(
    #                 subject=subject,
    #                 subject__section__class_obj=target_class,
    #             ).distinct().count()

    #             if all_sections_count != taught_sections_count:
    #                 raise serializers.ValidationError({
    #                     "teacher": _("لا يمكن ربط هذا المعلم بالامتحان لأنه لا يدرس هذه المادة في جميع شعب الصف المستهدف.")
    #                 })

    #         # الشرط الثاني: امتحان لصف مع نوع مسار محدد
    #         elif not target_section and stream_type:
    #             # حساب عدد الشعب في الصف التي لها نوع المسار المحدد
    #             all_stream_sections_count = Section.objects.filter(
    #                 class_obj=target_class,
    #                 stream_type=stream_type
    #             ).count()
                
    #             # حساب عدد الشعب التي يدرس فيها المعلم المادة من نفس المسار
    #             taught_stream_sections_count = teacher.teaching_subjects.filter(
    #                 subject=subject,
    #                 subject__section__class_obj=target_class,
    #                 subject__section__stream_type=stream_type,
    #             ).distinct().count()

    #             if all_stream_sections_count != taught_stream_sections_count:
    #                 raise serializers.ValidationError({
    #                     "teacher": _("لا يمكن ربط هذا المعلم بالامتحان لأنه لا يدرس هذه المادة في جميع شعب المسار المحددة في الصف.")
    #                 })

    #     return data

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

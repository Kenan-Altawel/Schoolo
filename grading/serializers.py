# exams/serializers.py
from rest_framework import serializers
from .models import Exam
from subject.models import Subject 
from academic.models import AcademicYear, AcademicTerm 
from classes.models import Class, Section 
from classes.serializers import ClassSerializer, SectionSerializer
from academic.serializers import AcademicYearSerializer, AcademicTermSerializer

class SubjectNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']

class ExamSerializer(serializers.ModelSerializer):
    
    subject_details = SubjectNameSerializer(source='subject', read_only=True)
    academic_year_details = AcademicYearSerializer(source='academic_year', read_only=True)
    academic_term_details = AcademicTermSerializer(source='academic_term', read_only=True)
   
    target_class_details = ClassSerializer(source='target_class', read_only=True)
    target_section_details = SectionSerializer(source='target_section', read_only=True)
    
    exam_type_display = serializers.CharField(source='get_exam_type_display', read_only=True)
    stream_type_display = serializers.CharField(source='get_stream_type_display', read_only=True)

    class Meta:
        model = Exam
        fields = [
            'id', 'subject', 'subject_details', 
            'academic_year', 'academic_year_details', 
            'academic_term', 'academic_term_details', 
            'exam_type', 'exam_type_display', 'exam_date', 'total_marks',
            'target_class', 'target_class_details', 
            'target_section', 'target_section_details', 
            'stream_type', 'stream_type_display',
            'created_at', 'updated_at' 
        ]
        extra_kwargs = {
            'subject': {'write_only': True, 'required': True},
            'academic_year': {'write_only': True, 'required': True},
            'academic_term': {'write_only': True, 'required': True},
            'exam_type': {'write_only': True, 'required': True},
            'exam_date': {'write_only': True, 'required': True},
            'total_marks': {'write_only': True, 'required': True},
            'target_class': {'write_only': True, 'required': False},
            'target_section': {'write_only': True, 'required': False},
            'stream_type': {'write_only': True, 'required': False},
        }

    def validate(self, data):
        """
        استدعاء دالة clean() للنموذج لفرض قيود التحقق المخصصة.
        """
        instance = Exam(**data) # إنشاء كائن مؤقت للتحقق
        if self.instance: # إذا كان هناك كائن موجود (تعديل)
            instance.pk = self.instance.pk # تعيين PK لتجاهل الكائن الحالي في clean
        
        try:
            instance.clean()
        except serializers.ValidationError as e: 
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            else:
                raise serializers.ValidationError({'non_field_errors': str(e)})
        except Exception as e:
            raise serializers.ValidationError({'non_field_errors': str(e)})

        return data
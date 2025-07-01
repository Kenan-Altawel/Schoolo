# subject/serializers.py
from rest_framework import serializers
from .models import Subject, SectionSubjectRequirement
from classes.models import Class, Section
from django.utils.translation import gettext_lazy as _

class SubjectSerializer(serializers.ModelSerializer):
    class_obj = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), allow_null=True, required=False)
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all(), allow_null=True, required=False)

    class_name = serializers.CharField(source='class_obj.name', read_only=True, required=False)
    section_name = serializers.CharField(source='section.name', read_only=True, required=False)

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'description', 'stream_type', 'is_active',
            'pdf_file',
            'class_obj', 'section', 'class_name', 'section_name',
            'default_weekly_lessons'
        ]

    def validate(self, data):
        class_obj = data.get('class_obj')
        section_obj = data.get('section')

        if class_obj and section_obj:
            if section_obj.class_obj != class_obj:
                raise serializers.ValidationError({"section": _("الشعبة المحددة لا تنتمي للفصل الدراسي المدخل.")})
        return data


class SectionSubjectRequirementSerializer(serializers.ModelSerializer):
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),

    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),

    )

    section_name = serializers.CharField(source='section.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    class_name = serializers.CharField(source='section.class_obj.name', read_only=True)

    class Meta:
        model = SectionSubjectRequirement
        fields = [
            'id', 'section', 'subject', 'weekly_lessons_required',
            'section_name', 'subject_name', 'class_name'
        ]
        read_only_fields = ['section_name', 'subject_name', 'class_name']
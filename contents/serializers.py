from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import SubjectContent, ContentAttachment

class ContentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentAttachment
        fields = '__all__'       

    def create(self, validated_data):
        instance = ContentAttachment(**validated_data)
        instance.full_clean() 
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean() 
        instance.save()
        return instance

class SubjectContentSerializer(serializers.ModelSerializer):
    attachments = ContentAttachmentSerializer(many=True, read_only=True) 

    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    class_name = serializers.CharField(source='section.class_obj.name', read_only=True)
    class_id = serializers.IntegerField(source='section.class_obj.id', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    academic_term_name = serializers.CharField(source='academic_term.name', read_only=True)
    
    class Meta:
        model = SubjectContent
        fields = [
            'id', 'subject', 'teacher', 'section', 'title',
            'subject_name', 'teacher_name','class_name', 
            'class_id', 'section_name',  'academic_year_name','academic_term_name',
            'attachments',
        ]
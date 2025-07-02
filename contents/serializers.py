from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

# تأكد من استيراد الموديلات التي تحتاجها
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

    class Meta:
        model = SubjectContent
        fields = [
            'id', 'subject', 'teacher', 'section', 'title',
            'subject_name', 'teacher_name', 'section_name', 
            'attachments'
        ]
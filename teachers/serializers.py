# teachers/serializers.py

from rest_framework import serializers
from .models import Teacher, TeacherAvailability
from django.utils.translation import gettext_lazy as _
from subject.models import TeacherSubject
from django.db import transaction

class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = TeacherAvailability
        fields = [ 'day_name']

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()
   
class TeacherProfileUpdateSerializer(serializers.ModelSerializer):
    address = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        label=_("العنوان")
    )
   
    availability = TeacherAvailabilitySerializer(
        many=True,
        required=False,
        label=_("توفر المعلم")
    )

    class Meta:
        model = Teacher
        fields = ['address',  'availability'] 
    def update(self, instance, validated_data):
        instance.address = validated_data.get('address', instance.address)
        instance.save()

        availability_data = validated_data.get('availability')
        if availability_data is not None:
            instance.availability.all().delete() 
            for availability_item_data in availability_data:
                TeacherAvailability.objects.create(teacher=instance, **availability_item_data)

        return instance
    

class TeacherListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ['user_id', 'full_name', 'specialization']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    
class TeacherSubjectSerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()

    class Meta:
        model = TeacherSubject
        fields = ['subject_id', 'subject_name', 'weekly_hours']

    def get_subject_name(self, obj):
        return obj.subject.name
    

class ManagerTeacherUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    is_active = serializers.BooleanField(source='user.is_active', required=False)
    phone_number = serializers.CharField(source='user.phone_number', required=False)
    
    class Meta:
        model = Teacher
        fields = [
            'first_name', 'last_name', 'phone_number', 'is_active',
            'address', 'specialization'
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        return super().update(instance, validated_data)

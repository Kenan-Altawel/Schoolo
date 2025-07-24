# teachers/serializers.py

from rest_framework import serializers
from .models import Teacher, TeacherAvailability
from django.utils.translation import gettext_lazy as _

class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = ['day_of_week']

   
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
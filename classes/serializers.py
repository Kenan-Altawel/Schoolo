from rest_framework import serializers
from academic.models import AcademicYear 
from .models import Class, Section
from django.utils.translation import gettext_lazy as _

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'

class SectionSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)

    class Meta:
        model = Section
        fields = [
            'id', 'name', 'stream_type', 'capacity', 'is_active',
            'activation_date', 'deactivation_date',
            'academic_year_name', 'class_name'
        ]
        read_only_fields = ['academic_year', 'class_obj', 'activation_date', 'deactivation_date']

    def create(self, validated_data):
        class_obj = self.context.get('class_obj')
        if not class_obj:
            raise serializers.ValidationError({"detail": _("Class object must be provided in the context for creating a section.")})

        validated_data['class_obj'] = class_obj 

        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            raise serializers.ValidationError({"academic_year": _("لا يوجد عام دراسي حالي محدد. الرجاء تحديد عام دراسي حالي أولاً.")})
        except AcademicYear.MultipleObjectsReturned:
            raise serializers.ValidationError({"academic_year": _("يوجد أكثر من عام دراسي حالي. الرجاء مراجعة البيانات.")})

        validated_data['academic_year'] = current_academic_year

        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('academic_year', None)
        validated_data.pop('class_obj', None)
        return super().update(instance, validated_data)
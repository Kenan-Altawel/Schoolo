from rest_framework import serializers
from academic.models import AcademicYear 
from .models import Class, Section
from django.utils.translation import gettext_lazy as _

class ClassSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'description', 'sections_count']

    def get_sections_count(self, obj):
        """
        يحسب عدد الشعب التابعة لهذا الفصل.
        """
        return obj.sections.count()

class SectionSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    class_id = serializers.IntegerField(source='class_obj.id', read_only=True)
    remaining_capacity = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            'id', 'name', 'stream_type', 'capacity', 'students_count', 'remaining_capacity', 'is_active',
            'activation_date', 'deactivation_date',
            'academic_year_name', 'class_name', 'class_id',
        ]
        read_only_fields = ['academic_year', 'class_obj', 'activation_date', 'deactivation_date']

    def get_remaining_capacity(self, obj):
        if obj.capacity is not None:
            return obj.capacity - obj.students_count
        return None
    
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
    

class TaughtClassSerializer(serializers.ModelSerializer):
    """سيريالايزر بسيط لعرض اسم الفصل الدراسي فقط."""
    class Meta:
        model = Class
        fields = ['id', 'name']

class TaughtSectionSerializer(serializers.ModelSerializer):
    """سيريالايزر لعرض الشعبة والصف المرتبط بها."""
    students_count = serializers.SerializerMethodField(read_only=True)
    class_obj = TaughtClassSerializer(read_only=True)
    class Meta:
        model = Section
        fields = ['id', 'name', 'class_obj','students_count']

    def get_students_count(self, obj):
        """
        يحسب عدد الطلاب في الشعبة.
        """
        return obj.students.count()

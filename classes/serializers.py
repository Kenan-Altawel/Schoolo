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
    
    def validate(self, data):
        instance = self.instance
        class_obj = self.context.get('class_obj') or (instance.class_obj if instance else None)
        
        if not class_obj:
            raise serializers.ValidationError({"detail": _("Class object must be provided.")})
        
        # جلب العام الدراسي الحالي
        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            raise serializers.ValidationError({"academic_year": _("لا يوجد عام دراسي حالي محدد. الرجاء تحديد عام دراسي حالي أولاً.")})
        except AcademicYear.MultipleObjectsReturned:
            raise serializers.ValidationError({"academic_year": _("يوجد أكثر من عام دراسي حالي. الرجاء مراجعة البيانات.")})
            
        academic_year = current_academic_year
        
        name = data.get('name', instance.name if instance else None)
        queryset = Section.objects.filter(name=name, class_obj=class_obj, academic_year=academic_year)
        
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise serializers.ValidationError({"name": _("الشعبة بهذا الاسم موجودة بالفعل في هذا الفصل الدراسي وهذا العام.")})
            
        stream_type_to_add = data.get('stream_type', instance.stream_type if instance else None)
        
        existing_streams = class_obj.sections.filter(academic_year=academic_year).values_list('stream_type', flat=True)
        existing_streams_set = set(existing_streams)

        if instance and instance.stream_type in existing_streams_set:
            existing_streams_set.remove(instance.stream_type)

        is_general_to_add = stream_type_to_add == 'General'
        is_general_in_class = 'General' in existing_streams_set
        is_specialized_to_add = stream_type_to_add in ['Scientific', 'Literary']
        is_specialized_in_class = 'Scientific' in existing_streams_set or 'Literary' in existing_streams_set
        
        if is_general_to_add and is_specialized_in_class:
            raise serializers.ValidationError({
                "stream_type": _("لا يمكن إضافة شعبة عامة إلى صف يحتوي على شعب علمية أو أدبية.")
            })
        
        if is_specialized_to_add and is_general_in_class:
            raise serializers.ValidationError({
                "stream_type": _("لا يمكن إضافة شعبة علمية أو أدبية إلى صف يحتوي على شعبة عامة.")
            })
        
        return data

    def create(self, validated_data):
        class_obj = self.context.get('class_obj')
        
        # جلب العام الدراسي الحالي
        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except (AcademicYear.DoesNotExist, AcademicYear.MultipleObjectsReturned) as e:
            raise serializers.ValidationError({"academic_year": str(e)})

        validated_data['class_obj'] = class_obj
        validated_data['academic_year'] = current_academic_year
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('academic_year', None)
        validated_data.pop('class_obj', None)
        return super().update(instance, validated_data)


class TaughtClassSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField(read_only=True)

    """سيريالايزر بسيط لعرض اسم الفصل الدراسي فقط."""
    class Meta:
        model = Class
        fields = ['id', 'name','description','sections_count']

    def get_sections_count(self, obj):
        teacher_instance = self.context.get('teacher_instance')
        
        # إذا كان المعلم موجودًا، قم بالعد بناءً على الشعب التي يدرسها
        if teacher_instance:
            return obj.sections.filter(class_schedules__teacher=teacher_instance).distinct().count()
        
        return 0
    
class TaughtSectionSerializer(serializers.ModelSerializer):
    """سيريالايزر لعرض الشعبة والصف المرتبط بها."""
    students_count = serializers.SerializerMethodField(read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    class_id = serializers.IntegerField(source='class_obj.id', read_only=True)
    class Meta:
        model = Section
        fields = ['id', 'name','class_id', 'class_name','stream_type','capacity','students_count']

    def get_students_count(self, obj):
        """
        يحسب عدد الطلاب في الشعبة.
        """
        return obj.students.count()

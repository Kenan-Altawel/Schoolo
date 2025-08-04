# your_app_name/serializers.py
from rest_framework import serializers
from .models import AcademicYear, AcademicTerm

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = '__all__' 

class AcademicTermSerializer(serializers.ModelSerializer): 
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True) 

    class Meta:
        model = AcademicTerm
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current', 'academic_year_name']
        read_only_fields = ['academic_year'] 

    def create(self, validated_data):
        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            raise serializers.ValidationError({"academic_year": "لا يوجد عام دراسي حالي محدد."})
        except AcademicYear.MultipleObjectsReturned:
            raise serializers.ValidationError({"academic_year": "يوجد أكثر من عام دراسي حالي، الرجاء مراجعة البيانات."})

        validated_data['academic_year'] = current_academic_year
        return super().create(validated_data)
    
from .models import TimeSlot, DayOfWeek

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = '__all__' 
        read_only_fields = ('created_at',) 

class DayOfWeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOfWeek
        fields = '__all__' 
        read_only_fields = ('created_at',)
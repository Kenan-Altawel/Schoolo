# subject/filters.py
import django_filters
from .models import Subject
from classes.models import Class, Section 

class SubjectFilter(django_filters.FilterSet):
    # فلترة حسب الاسم (بحث جزئي وغير حساس لحالة الأحرف)
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    # فلترة حسب معرف الصف (Class ID)
    class_id = django_filters.NumberFilter(field_name='class_obj__id', lookup_expr='exact')

    # فلترة حسب معرف الشعبة (Section ID)
    section_id = django_filters.NumberFilter(field_name='section__id', lookup_expr='exact')

    class Meta:
        model = Subject
        fields = ['name', 'class_id', 'section_id', 'stream_type', 'is_active']
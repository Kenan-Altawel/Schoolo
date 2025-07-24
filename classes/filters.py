# classes/filters.py 
import django_filters
from .models import Section, Class 
from academic.models import AcademicYear 

class SectionFilter(django_filters.FilterSet):
    class_id = django_filters.NumberFilter(field_name='class_obj__id', lookup_expr='exact')
    academic_year_id = django_filters.NumberFilter(field_name='academic_year__id', lookup_expr='exact')
    academic_year_name = django_filters.CharFilter(field_name='academic_year__name', lookup_expr='icontains')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    class Meta:
        model = Section
        fields = ['class_id', 'academic_year_id', 'name', 'stream_type', 'is_active']


class ClassFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Class
        fields = ['name'] 
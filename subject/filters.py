# subject/filters.py
import django_filters
from .models import Subject
from classes.models import Class, Section 

class SubjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class_id = django_filters.NumberFilter(field_name='class_obj__id', lookup_expr='exact')

    section_id = django_filters.NumberFilter(field_name='section__id', lookup_expr='exact')

    class Meta:
        model = Subject
        fields = ['name', 'class_id', 'section_id', 'stream_type', 'is_active']
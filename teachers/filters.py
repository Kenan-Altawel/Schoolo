# في ملف filters.py

import django_filters
from .models import Teacher

class TeacherFilter(django_filters.FilterSet):
   
    first_name = django_filters.CharFilter(
        field_name='first_name',
        lookup_expr='icontains',
    )
    last_name = django_filters.CharFilter(
        field_name='user__last_name',
        lookup_expr='icontains'
    )
    specialization = django_filters.CharFilter(
        field_name='specialization',
        lookup_expr='icontains'
    )
    
    class Meta:
        model = Teacher
        fields = ['specialization', 'first_name', 'last_name']
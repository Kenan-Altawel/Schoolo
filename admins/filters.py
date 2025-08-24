# في ملف filters.py

import django_filters
from .models import Admin

class TeacherFilter(django_filters.FilterSet):
   
    first_name = django_filters.CharFilter(
        field_name='first_name',
        lookup_expr='icontains',
    )
    last_name = django_filters.CharFilter(
        field_name='user__last_name',
        lookup_expr='icontains'
    )
    department = django_filters.CharFilter(
        field_name='department',
        lookup_expr='icontains'
    )
    
    class Meta:
        model = Admin
        fields = ['department', 'first_name', 'last_name']
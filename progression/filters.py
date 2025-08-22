# progression/filters.py
import django_filters
from .models import StudentProgressionIssue

class StudentProgressionIssueFilterSet(django_filters.FilterSet):
    from_class = django_filters.NumberFilter(
        field_name='student_progression__student__student_class__id',
        label="ID of the student's class"
    )
    from_section = django_filters.NumberFilter(
        field_name='student_progression__student__section__id',
        label="ID of the student's section"
    )
    issue_type = django_filters.CharFilter(
        field_name='issue_type',
        lookup_expr='exact',
        label="Type of the issue (e.g., 'no_available_section')"
    )

    class Meta:
        model = StudentProgressionIssue
        fields = ['from_class', 'from_section', 'issue_type']

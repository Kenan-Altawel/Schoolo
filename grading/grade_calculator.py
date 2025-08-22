from django.db.models import Avg, Sum
from students.models import Student
from .models import Grade
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class GradeCalculator:
    """
    كلاس مسؤول عن حساب معدلات الطلاب
    """

    def _get_base_queryset(self, student_id, academic_year_id=None, academic_term_id=None, subject_id=None):
        """
        دالة مساعدة لإنشاء QuerySet الأساسي
        """
        grades_queryset = Grade.objects.filter(student_id=student_id)
        if academic_year_id:
            grades_queryset = grades_queryset.filter(exam__academic_year_id=academic_year_id)
        if academic_term_id:
            grades_queryset = grades_queryset.filter(exam__academic_term_id=academic_term_id)
        if subject_id:
            grades_queryset = grades_queryset.filter(exam__subject_id=subject_id)
        return grades_queryset

    def _normalized_percentage_for_queryset(self, grades_queryset):
        """
        يحسب نسبة مئوية موحّدة (0-100) باحتساب مجموع العلامات ÷ مجموع العلامات الكلية ثم * 100.
        يعيد None إذا لا توجد بيانات أو المجموع الكلي يساوي صفرًا.
        """
        aggregates = grades_queryset.aggregate(
            total_score=Sum('score'),
            total_max=Sum('exam__total_marks'),
        )
        total_score = aggregates['total_score']
        total_max = aggregates['total_max']
        if total_score is None or total_max in (None, Decimal('0')):
            return None
        percent = (Decimal(total_score) / Decimal(total_max)) * Decimal('100')
        return round(percent, 2)

    def calculate_subject_average(self, student_id, subject_id, academic_year_id=None, academic_term_id=None):
        """
        يحسب المعدل كنسبة مئوية موحّدة لمادة محددة ضمن القيود (سنة/فصل اختياريين).
        """
        grades_queryset = self._get_base_queryset(
            student_id,
            academic_year_id=academic_year_id,
            academic_term_id=academic_term_id,
            subject_id=subject_id,
        )
        return self._normalized_percentage_for_queryset(grades_queryset)

    def calculate_overall_average(self, student_id, academic_year_id=None, academic_term_id=None):
        """
        يحسب المعدل العام عبر جميع المواد على شكل متوسط معدلات المواد (كنسب مئوية).
        كل مادة تُحسب كنسبة مئوية موحّدة ضمن نفس القيود، ثم نأخذ متوسط هذه النسب.
        """
        base_qs = Grade.objects.filter(student_id=student_id)

        if academic_term_id:
            base_qs = base_qs.filter(exam__academic_term_id=academic_term_id)
        elif academic_year_id:
            base_qs = base_qs.filter(exam__academic_term__academic_year_id=academic_year_id)
        else:
            return None
        
        if not base_qs.exists():
            return None
        
        subject_ids = (
            base_qs
            .values_list('exam__subject_id', flat=True)
            .distinct()
        )
        per_subject_avgs = []
        for sid in subject_ids:
            subject_qs = base_qs.filter(exam__subject_id=sid)
            avg_percent = self._normalized_percentage_for_queryset(subject_qs)
            if avg_percent is not None:
                per_subject_avgs.append(avg_percent)

        if not per_subject_avgs:
            return None

        overall = sum(per_subject_avgs) / len(per_subject_avgs)
        return round(overall, 2)
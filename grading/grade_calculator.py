from django.db.models import Avg
from students.models import Student
from .models import Grade
from django.utils.translation import gettext_lazy as _

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

    def calculate_activities_average(self, student_id, academic_year_id, academic_term_id, subject_id):
        grades_queryset = self._get_base_queryset(student_id, academic_year_id, academic_term_id, subject_id)
        activities_grades = grades_queryset.filter(exam__exam_type__in=['quiz', 'assignment'])
        average_score = activities_grades.aggregate(Avg('score'))['score__avg']
        return round(average_score, 2) if average_score is not None else None

    def calculate_midterm_average(self, student_id, academic_year_id, academic_term_id, subject_id):
        grades_queryset = self._get_base_queryset(student_id, academic_year_id, academic_term_id, subject_id)
        midterm_grades = grades_queryset.filter(exam__exam_type='midterm')
        average_score = midterm_grades.aggregate(Avg('score'))['score__avg']
        return round(average_score, 2) if average_score is not None else None

    def calculate_final_score(self, student_id, academic_year_id, academic_term_id, subject_id):
        grades_queryset = self._get_base_queryset(student_id, academic_year_id, academic_term_id, subject_id)
        final_grade = grades_queryset.filter(exam__exam_type='final').first()
        return round(final_grade.score, 2) if final_grade else None

    def calculate_total_term_average(self, student_id, academic_year_id, academic_term_id, subject_id):
        activities_avg = self.calculate_activities_average(student_id, academic_year_id, academic_term_id, subject_id)
        midterm_avg = self.calculate_midterm_average(student_id, academic_year_id, academic_term_id, subject_id)
        final_score = self.calculate_final_score(student_id, academic_year_id, academic_term_id, subject_id)

        # حساب المعدل الإجمالي بناءً على الأوزان (20% أنشطة, 30% نصفي, 50% نهائي)
        total_average = None
        if activities_avg is not None and midterm_avg is not None and final_score is not None:
            total_average = (activities_avg * 0.20) + (midterm_avg * 0.30) + (final_score * 0.50)
        
        return round(total_average, 2) if total_average is not None else None
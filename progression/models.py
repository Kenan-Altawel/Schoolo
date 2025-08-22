# progression/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from academic.models import AcademicYear
from students.models import Student
from classes.models import Class, Section  # إعادة استيراد النماذج
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel

class StudentProgression(AutoCreateAndAutoUpdateTimeStampedModel):
    """
    نموذج لتسجيل حالة تقدم الطالب في نهاية كل عام دراسي.
    """
    RESULT_STATUS_CHOICES = [
        ('promoted', _('ناجح')),
        ('failed', _('راسب')),
        ('graduated', _('متخرج')),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='progression_records',
        verbose_name=_("الطالب")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='student_progressions',
        verbose_name=_("العام الدراسي")
    )
    overall_average = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("المعدل العام")
    )
    result_status = models.CharField(
        max_length=20,
        choices=RESULT_STATUS_CHOICES,
        verbose_name=_("حالة النتيجة")
    )
    is_promoted = models.BooleanField(
        default=False,
        verbose_name=_("هل تم ترقيته؟"),
        help_text=_("يشير إلى ما إذا كان الطالب قد تم ترقيته إلى صف أعلى.")
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("ملاحظات")
    )
    from_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL, 
        related_name='progression_from',
        null=True,
        blank=True,
        verbose_name=_("من الصف")
    )
    from_section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        related_name='progression_from',
        null=True,
        blank=True,
        verbose_name=_("من الشعبة")
    )
    to_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        related_name='progression_to',
        null=True,
        blank=True,
        verbose_name=_("إلى الصف")
    )
    to_section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        related_name='progression_to',
        null=True,
        blank=True,
        verbose_name=_("إلى الشعبة")
    )

    class Meta:
        verbose_name = _("تقدم الطالب")
        verbose_name_plural = _("سجلات تقدم الطلاب")
        unique_together = ['student', 'academic_year']
        ordering = ['-academic_year__start_date', 'student__user__first_name']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.academic_year.name} ({self.get_result_status_display()})"


class StudentProgressionIssue(AutoCreateAndAutoUpdateTimeStampedModel):
    """
    نموذج لتسجيل المشاكل التي تحدث أثناء عملية الترقية التلقائية.
    """
    ISSUE_TYPE_CHOICES = [
        ('section_capacity_full', _('سعة الشعبة ممتلئة')),
        ('no_available_section', _('لا توجد شعبة متاحة')),
        ('inactive_section', _('الشعبة غير نشطة')),
    ]

    student_progression = models.OneToOneField(
        StudentProgression,
        on_delete=models.CASCADE,
        related_name='issue',
        verbose_name=_("سجل التقدم")
    )
    issue_type = models.CharField(
        max_length=50,
        choices=ISSUE_TYPE_CHOICES,
        verbose_name=_("نوع المشكلة")
    )
    description = models.TextField(
        verbose_name=_("الوصف")
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name=_("تم الحل؟")
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاريخ الحل")
    )

    class Meta:
        verbose_name = _("مشكلة تقدم طالب")
        verbose_name_plural = _("مشاكل تقدم الطلاب")
        ordering = ['-created_at']

    def __str__(self):
        return f"مشكلة لـ {self.student_progression.student.user.get_full_name()} - {self.get_issue_type_display()}"


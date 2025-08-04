# academic/models.py
# (تكملة لنفس الملف الذي يحتوي على AcademicYear, AcademicTerm, Class, Section, Subject, Course, SubjectContent)

from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel
from teachers.models import Teacher # للتأكد من استيراد Teacher
from subject.models import Subject
from classes.models import Section
from academic.models import AcademicTerm,AcademicYear, DayOfWeek, TimeSlot

class ProposedClassSchedule(AutoCreateAndAutoUpdateTimeStampedModel):
    DAY_OF_WEEK_CHOICES = [
        ('Monday', _('الاثنين')),
        ('Tuesday', _('الثلاثاء')),
        ('Wednesday', _('الأربعاء')),
        ('Thursday', _('الخميس')),
        ('Friday', _('الجمعة')),
        ('Saturday', _('السبت')),
        ('Sunday', _('الأحد')),
    ]

    SCHEDULE_STATUS_CHOICES = [
        ('proposed', _('مقترح')),
        ('accepted', _('مقبول')),
        ('rejected', _('مرفوض')),
    ]

    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE,
        related_name='proposed_schedules',
        verbose_name=_("المادة الدراسية")
    )
    section = models.ForeignKey(
        Section, 
        on_delete=models.CASCADE,
        related_name='proposed_schedules',
        verbose_name=_("القسم")
    )
    teacher = models.ForeignKey(
        Teacher, # المعلم الذي سيقوم بالتدريس
        on_delete=models.SET_NULL, # لا تحذف الجدول إذا حُذف المعلم
        null=True,
        blank=True,
        related_name='proposed_teaching_schedules',
        verbose_name=_("المعلم")
    )
    academic_year = models.ForeignKey(
        AcademicYear, 
        on_delete=models.CASCADE,
        related_name='proposed_schedules',
        verbose_name=_("العام الدراسي")
    )
    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='proposed_schedules',
        verbose_name=_("الفصل الدراسي")
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DAY_OF_WEEK_CHOICES,
        verbose_name=_("يوم الأسبوع"),
        help_text=_("اليوم الذي ستقام فيه الحصة.")
    )
    period = models.CharField(
        max_length=50, 
        verbose_name=_("الفترة/الحصة"),
        help_text=_("توقيت الحصة أو رقم الفترة (مثال: '08:00-09:00' أو 'الفترة الأولى').")
    )
    status = models.CharField(
        max_length=10,
        choices=SCHEDULE_STATUS_CHOICES,
        default='proposed',
        verbose_name=_("الحالة"),
        help_text=_("حالة المقترح: مقترح، مقبول، مرفوض.")
    )

    class Meta:
        verbose_name = _("جدول حصص مقترح")
        verbose_name_plural = _("جداول الحصص المقترحة")
        ordering = ['academic_year', 'academic_term', 'section', 'day_of_week', 'period']

        unique_together = [
            ['subject', 'section', 'academic_year', 'academic_term', 'day_of_week', 'period']
        ]

    def __str__(self):
        return (
            f"{self.subject.name} - {self.section.name} - {self.get_day_of_week_display()} "
            f"({self.period}) - {self.academic_term.name}, {self.academic_year.name}"
        )
    
class ClassSchedule(AutoCreateAndAutoUpdateTimeStampedModel):
    
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE,
        related_name='class_schedules',
        verbose_name=_("المادة الدراسية")
    )
    section = models.ForeignKey(
        Section, 
        on_delete=models.CASCADE,
        related_name='class_schedules',
        verbose_name=_("القسم")
    )
    teacher = models.ForeignKey(
        Teacher, # المعلم الذي سيقوم بالتدريس
        on_delete=models.SET_NULL, # لا تحذف الجدول إذا حُذف المعلم
        null=True,
        blank=True,
        related_name='teaching_schedules',
        verbose_name=_("المعلم")
    )
    academic_year = models.ForeignKey(
        AcademicYear, # العام الدراسي للجدول
        on_delete=models.CASCADE,
        related_name='class_schedules',
        verbose_name=_("العام الدراسي")
    )
    academic_term = models.ForeignKey(
        AcademicTerm, # الفصل الدراسي للجدول
        on_delete=models.CASCADE,
        related_name='class_schedules',
        verbose_name=_("الفصل الدراسي")
    )
    day_of_week = models.ForeignKey(
        DayOfWeek,
        on_delete=models.CASCADE,
        related_name='class_schedules',
        verbose_name=_("يوم الأسبوع")
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='class_schedules',
        verbose_name=_("الفترة الزمنية")
    )
    class Meta:
        verbose_name = _("جدول حصص معتمد")
        verbose_name_plural = _("جداول الحصص المعتمدة")
        ordering = ['academic_year', 'academic_term', 'section', 'day_of_week', 'time_slot']

        unique_together = [
            ['subject', 'section', 'academic_year', 'academic_term', 'day_of_week', 'time_slot']
        ]

    def __str__(self):
        return (
            f"{self.subject.name} - {self.section.name} - {self.day_of_week} "
            f"({self.time_slot}) - {self.academic_term.name}, {self.academic_year.name}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        existing_schedules = ClassSchedule.objects.filter(
            teacher=self.teacher,
            academic_year=self.academic_year,
            academic_term=self.academic_term,
            day_of_week=self.day_of_week,
            time_slot=self.time_slot
        ).exclude(pk=self.pk) 

        if existing_schedules.exists():
            raise ValidationError(
                _("هذا المعلم لديه حصة أخرى في نفس اليوم والفترة والفصل الدراسي المحدد.")
            )

        # التحقق من عدم وجود تداخل في جدول القسم (Section Clash)
        # لا يمكن لنفس القسم أن يكون لديه حصتين في نفس اليوم والفترة في نفس العام/الفصل الدراسي
        existing_schedules_for_section = ClassSchedule.objects.filter(
            section=self.section,
            academic_year=self.academic_year,
            academic_term=self.academic_term,
            day_of_week=self.day_of_week,
            time_slot=self.time_slot
        ).exclude(pk=self.pk) # استبعاد الكائن الحالي في حالة التحديث

        if existing_schedules_for_section.exists():
            raise ValidationError(
                _("هذا القسم لديه حصة أخرى في نفس اليوم والفترة والفصل الدراسي المحدد.")
            )

        super().clean()

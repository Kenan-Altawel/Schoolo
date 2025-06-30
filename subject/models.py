from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel, User
from classes.models import Class,Section
from django.utils.translation import gettext_lazy as _
from teachers.models import Teacher
from django.core.exceptions import ValidationError

class Subject(AutoCreateAndAutoUpdateTimeStampedModel):
    STREAM_TYPE_CHOICES = [
        ('Scientific', _('علمي')),
        ('Literary', _('أدبي')),
        ('General', _('عام')),
    ]

    class_obj = models.ForeignKey( 
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects_in_class',
        verbose_name=_("الفصل الدراسي المرتبط"),
        help_text=_("الفصل الدراسي الذي تنتمي إليه هذه المادة (مثال: الصف الأول).")
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects_in_section',
        verbose_name=_("القسم المرتبط"),
        help_text=_("القسم الذي تنتمي إليه هذه المادة (مثال: القسم أ).")
    )

    stream_type = models.CharField(
        max_length=50,
        choices=STREAM_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("نوع المسار"),
        help_text=_("نوع المسار إذا كانت المادة خاصة بمسار معين (علمي/أدبي).")
    )
    name = models.CharField(
        max_length=150,
        verbose_name=_("اسم المادة")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("الوصف التفصيلي للمادة")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("هل المادة نشطة؟"),
        help_text=_("يشير إلى ما إذا كانت هذه المادة متاحة للتدريس.")
    )
    pdf_url = models.URLField( 
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("رابط ملف الـ PDF"),
        help_text=_("رابط للمنهج الدراسي أو مواد مساعدة بصيغة PDF.")
    )
    weekly_sessions = models.IntegerField(
        verbose_name=_("عدد الحصص الأسبوعية"),
        help_text=_("عدد الحصص المخصصة لهذه المادة أسبوعياً.")
    )

    class Meta:
        verbose_name = _("مادة دراسية")
        verbose_name_plural = _("المواد الدراسية")
        ordering = ['name']

        
      
    def _str_(self):
        return f"{self.name} "



class TeacherSubject(AutoCreateAndAutoUpdateTimeStampedModel):
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE,
        related_name='teaching_subjects',
        verbose_name=_("المعلم")
    )
    subject = models.ForeignKey(
        Subject, # يشير إلى نموذج Subject من تطبيق subjects
        on_delete=models.CASCADE,
        related_name='taught_by_teachers',
        verbose_name=_("المادة الدراسية")
    )
    weekly_hours = models.PositiveIntegerField(
        verbose_name=_("الساعات الأسبوعية"),
        help_text=_("عدد الساعات الأسبوعية التي يدرسها المعلم لهذه المادة.")
    )

    class Meta:
        verbose_name = _("مادة المعلم")
        verbose_name_plural = _("مواد المعلمين")
        unique_together = [
            ['teacher', 'subject']
        ]
        # ordering = ['teacher_first_name']

    def _str_(self):
        return f"{self.teacher.user.get_full_name()} يدرس {self.subject.name} ({self.weekly_hours} ساعة/أسبوع)"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.weekly_hours <= 0:
            raise ValidationError(
                _("يجب أن تكون عدد الساعات الأسبوعية أكبر من صفر.")
            )
        
        super().clean()

#####################################################################################
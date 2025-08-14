# subject/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from academic.models import AcademicTerm, AcademicYear
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel, User
from classes.models import Class,Section
from teachers.models import Teacher
from django.core.exceptions import ValidationError

class SubjectIcon(AutoCreateAndAutoUpdateTimeStampedModel):
    """
    موديل لتخزين أيقونات المواد الدراسية.
    """
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("اسم الأيقونة")
    )
    icon_file = models.ImageField(
        upload_to='subject/subject_files/icons/',
        verbose_name=_("ملف الأيقونة"),
        help_text=_("تحميل ملف الأيقونة كصورة (يفضل صيغة SVG أو PNG).")
    )

    class Meta:
        verbose_name = _("أيقونة المادة")
        verbose_name_plural = _("أيقونات المواد")

    def __str__(self):
        return self.name
    
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
        null=True, blank=True, 
        related_name='subjects_in_section',
        verbose_name=_(" الشعبة"),
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
    pdf_file = models.FileField( 
        upload_to='subject/subject_files/subject_pdfs/',
        blank=True,
        null=True,
        verbose_name=_("ملف المنهج الدراسي PDF"),
        help_text=_("رفع ملف المنهج الدراسي أو مواد مساعدة بصيغة PDF.")
    )
    icon = models.ForeignKey(
        SubjectIcon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects_with_icon',
        verbose_name=_("أيقونة المادة")
    )    
    default_weekly_lessons = models.PositiveIntegerField(
        verbose_name=_("عدد الحصص الأسبوعية الافتراضي"),
        default=0,
        help_text=_("عدد الحصص الأسبوعية الافتراضي لهذه المادة، يستخدم عند عدم تحديد عدد معين للشعبة.")
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='subjects_in_year',
        verbose_name=_("العام الدراسي")
    )

    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='subjects_in_term',
        verbose_name=_("الفصل الدراسي")
    )

    class Meta:
        verbose_name = _("مادة دراسية")
        verbose_name_plural = _("المواد الدراسية")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['class_obj', 'stream_type', 'name', 'academic_year', 'academic_term'],
                condition=models.Q(section__isnull=True), 
                name='unique_subject_per_class_and_stream_term'
            ),
            models.UniqueConstraint(
                fields=['section', 'name', 'academic_year', 'academic_term'],
                condition=models.Q(class_obj__isnull=True, stream_type__isnull=True), 
                name='unique_subject_per_section_term'
            ),
        ]

    def __str__(self):
        return f"{self.name}"


class TeacherSubject(AutoCreateAndAutoUpdateTimeStampedModel):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='teaching_subjects',
        verbose_name=_("المعلم")
    )
    subject = models.ForeignKey(
        Subject,
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

    def __str__(self):
        return f"{self.teacher.user.get_full_name()} يدرس {self.subject.name} ({self.weekly_hours} ساعة/أسبوع)"


#####################################################################################

class SectionSubjectRequirement(models.Model):
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='section_requirements',
        verbose_name=_("الشعبة")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='subject_requirements',
        verbose_name=_("المادة")
    )

    weekly_lessons_required = models.IntegerField(
        help_text=_('عدد الحصص الأسبوعية المطلوبة لهذه المادة في هذه الشعبة'),
        verbose_name=_("عدد الحصص الأسبوعية المطلوبة")
    )

    class Meta:
        unique_together = ('section', 'subject')
        verbose_name = _("متطلب حصص الشعبة")
        verbose_name_plural = _("متطلبات حصص الشعب")

    def __str__(self):
        section_name = self.section.name if hasattr(self.section, 'name') else 'N/A'
        subject_name = self.subject.name if hasattr(self.subject, 'name') else 'N/A'
        return f"{section_name} - {subject_name}: {self.weekly_lessons_required} {(_('حصص أسبوعياً'))}"
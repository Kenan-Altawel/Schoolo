from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel,User
from schedules.models import ClassSchedule
from subject.models import Subject
from academic.models import AcademicYear, AcademicTerm
from classes.models import Class, Section 
from students.models import Student
import datetime
from django.db.models import Q

from teachers.models import Teacher

class Exam(AutoCreateAndAutoUpdateTimeStampedModel):
    EXAM_TYPE_CHOICES = [
        ('midterm', _('اختبار منتصف الفصل')),
        ('final', _('اختبار نهائي')),
        ('quiz', _('اختبار قصير')),
        ('assignment', _('واجب')),
        
    ]

    STREAM_TYPE_CHOICES = [
        ('General', _('عام')),
        ('Scientific', _('علمي')),
        ('Literary', _('أدبي')),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='exams',
        verbose_name=_("المادة الدراسية")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='exams',
        verbose_name=_("العام الدراسي")
    )
    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='exams',
        verbose_name=_("الفصل الدراسي")
    )
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        verbose_name=_("نوع الاختبار"),
        help_text=_("نوع الاختبار أو التقييم (مثال: اختبار نصفي، واجب، نهائي).")
    )
    exam_date = models.DateField(
        verbose_name=_("تاريخ الاختبار"),
        help_text=_("التاريخ الذي أقيم فيه الاختبار.")
    )
    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("الدرجة الكلية"),
        help_text=_("الدرجة الكلية الممكنة لهذا الاختبار.")
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exams_created',
        verbose_name=_("المعلم المسؤول"),
        help_text=_("المعلم المسؤول عن هذا الاختبار.")
    )
    
    target_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("الصف المستهدف"),
        help_text=_("الصف الذي يستهدفه هذا الاختبار (إذا لم يكن لجميع الصفوف).")
    )
    target_section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("الشعبة المستهدفة"),
        help_text=_("الشعبة المحددة داخل الصف المستهدف.")
    )
    is_conducted = models.BooleanField(
        default=False,
        verbose_name=_("هل تم إجراء الاختبار؟"),
        help_text=_("يشير إلى ما إذا كان الاختبار قد تم إجراؤه بالفعل.")
    )
    stream_type = models.CharField(
        max_length=20,
        choices=STREAM_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("نوع التخصص"),
        help_text=_("نوع التخصص المستهدف (مثال: علمي، أدبي) ضمن الصف المحدد.")
    )
    
    class Meta:
        verbose_name = _("اختبار")
        verbose_name_plural = _("الاختبارات")
        ordering = ['-exam_date', 'subject__name']
        unique_together = [
            ['subject', 'academic_year', 'academic_term', 'exam_type', 'exam_date', 'target_class', 'target_section', 'stream_type']
        ]

    def __str__(self):
        details = []
        if self.target_section:
            details.append(str(self.target_section.class_obj))
            details.append(str(self.target_section))
            details.append(self.target_section.get_stream_type_display())
        elif self.target_class:
            details.append(str(self.target_class))

        target_str = f"({', '.join(details)})" if details else "(عام لجميع الصفوف/الشعب/التخصصات)"

        return (
            f"{self.get_exam_type_display()} - {self.subject.name} "
            f"لـ {target_str} ({self.academic_term.name}, {self.academic_year.name}) - {self.exam_date}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        from subject.models import TeacherSubject

        if self.total_marks <= 0:
            raise ValidationError(_("يجب أن تكون الدرجة الكلية للاختبار أكبر من صفر."))
        
        if not (self.target_class or self.target_section):
            raise ValidationError(_("يجب تحديد الصف المستهدف على الأقل لإنشاء امتحان."))
         # التحقق من التناسق: لا يمكن تحديد شعبة ونوع تخصص في نفس الوقت
        if self.target_section and self.stream_type:
            raise ValidationError(_("لا يمكن تحديد شعبة محددة ونوع تخصص في نفس الوقت. اختر أحدهما فقط."))

        # التحقق من أن الشعبة تنتمي للصف المحدد
        if self.target_section and self.target_class and self.target_section.class_obj != self.target_class:
            raise ValidationError(_("الشعبة المستهدفة لا تنتمي إلى الصف المستهدف."))
        
        if self.target_class and self.stream_type:
            if not Section.objects.filter(class_obj=self.target_class, stream_type=self.stream_type).exists():
                 raise ValidationError(_("الصف المحدد لا يحتوي على شعب من نوع التخصص المحدد."))
        # التحقق من أن المعلم يدرس المادة المستهدفة
        if self.teacher and self.subject:
            if not TeacherSubject.objects.filter(teacher=self.teacher, subject=self.subject).exists():
                raise ValidationError(_("المعلم المحدد لا يدرس المادة المستهدفة لهذا الاختبار."))
        
        # التحقق من أن الشعبة تنتمي إلى الصف
        if self.target_section and self.target_class and self.target_section.class_obj != self.target_class:
            raise ValidationError(_("الشعبة المستهدفة يجب أن تنتمي إلى الصف المستهدف المحدد."))

        # التحقق من التضارب (الأساسي)
        # هذا الشرط يمنع وجود امتحانين بنفس المواصفات بالضبط
        conflicting_exams_query = Exam.objects.filter(
            subject=self.subject,
            academic_year=self.academic_year,
            academic_term=self.academic_term,
            exam_type=self.exam_type,
            exam_date=self.exam_date,
            target_class=self.target_class,
            target_section=self.target_section,
            stream_type=self.stream_type
        ).exclude(pk=self.pk)

        if conflicting_exams_query.exists():
            raise ValidationError(_("يوجد بالفعل امتحان بنفس المواصفات في نفس التاريخ."))
        if self.teacher and self.subject:
        # إذا كان الامتحان يستهدف شعبة محددة
            if self.target_section:
                has_schedule = ClassSchedule.objects.filter(
                    teacher=self.teacher,
                    subject=self.subject,
                    section=self.target_section,
                    academic_year=self.academic_year,
                    academic_term=self.academic_term
                ).exists()
                if not has_schedule:
                    raise ValidationError(
                        _("المعلم المحدد لا يدرس هذه المادة في الشعبة المستهدفة لهذا الفصل الدراسي.")
                    )
                # إذا كان الامتحان يستهدف صفًا كاملاً (جميع شعبه)
                elif self.target_class:
                    has_schedule = ClassSchedule.objects.filter(
                        teacher=self.teacher,
                        subject=self.subject,
                        section__class_obj=self.target_class,
                        academic_year=self.academic_year,
                        academic_term=self.academic_term
                    ).exists()
                    if not has_schedule:
                        raise ValidationError(
                            _("المعلم المحدد لا يدرس هذه المادة في أي شعبة من الصف المستهدف لهذا الفصل الدراسي.")
                        )
                # إذا كان الامتحان عاماً (لا يستهدف شعبة أو صف)
                else:
                    has_teacher_subject = TeacherSubject.objects.filter(
                        teacher=self.teacher,
                        subject=self.subject
                    ).exists()
                    if not has_teacher_subject:
                        raise ValidationError(
                            _("المعلم المحدد لا يدرس المادة المستهدفة لهذا الاختبار.")
                        )
        # التحقق من تضارب الوقت
        # هنا نتحقق من عدم وجود امتحان آخر في نفس الوقت لنفس الصف أو الشعبة
        conflicting_time_query = Exam.objects.filter(
            exam_date=self.exam_date,
            academic_year=self.academic_year,
            academic_term=self.academic_term
        ).exclude(pk=self.pk)

        if self.target_section:
            conflicting_time_query = conflicting_time_query.filter(
                Q(target_section=self.target_section) |
                Q(target_class=self.target_section.class_obj) |
                Q(target_section__class_obj=self.target_section.class_obj)
            )
        elif self.target_class:
            conflicting_time_query = conflicting_time_query.filter(
                Q(target_class=self.target_class) |
                Q(target_section__class_obj=self.target_class)
            )

        if conflicting_time_query.exists():
            raise ValidationError(_("يوجد امتحان آخر في نفس الوقت لهذه الشعبة أو الصف."))

        
        super().clean()




################################################GRADES#############################################################
class Grade(AutoCreateAndAutoUpdateTimeStampedModel):
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name=_("الطالب")
    )
    exam = models.ForeignKey(
        'Exam', 
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name=_("الاختبار")
    )
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name=_("الدرجة المحرزة"),
        help_text=_("الدرجة التي حصل عليها الطالب في هذا الاختبار.")
    )
    graded_at = models.DateTimeField( # متى تم تسجيل الدرجة
        null=True,
        blank=True,
        verbose_name=_("تاريخ ووقت التقييم"),
        help_text=_("التاريخ والوقت الذي تم فيه تسجيل الدرجة.")
    )

    class Meta:
        verbose_name = _("درجة")
        verbose_name_plural = _("الدرجات")
        unique_together = [
            ['student', 'exam']
        ]
        ordering = ['student__user__last_name']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.exam.get_exam_type_display()} ({self.score})"

    
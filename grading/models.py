from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel,User
from subject.models import Subject
from academic.models import AcademicYear, AcademicTerm
from classes.models import Class, Section 
from students.models import Student
import datetime

class Exam(AutoCreateAndAutoUpdateTimeStampedModel):
    EXAM_TYPE_CHOICES = [
        ('midterm', _('اختبار منتصف الفصل')),
        ('final', _('اختبار نهائي')),
        ('quiz', _('اختبار قصير')),
        ('assignment', _('واجب')),
        
    ]

    STREAM_TYPE_CHOICES = [
        ('scientific', _('علمي')),
        ('literary', _('أدبي')),
        ('general', _('عام')),
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
        # الأولوية للشعبة، لأنها الأكثر تحديداً
        if self.target_section:
            details.append(str(self.target_section.class_obj)) # الصف الذي تنتمي إليه الشعبة
            details.append(str(self.target_section)) # اسم الشعبة
            if self.target_section.stream_type:
                details.append(self.target_section.get_stream_type_display())
        elif self.target_class:
            details.append(str(self.target_class))
            if self.stream_type: 
                details.append(self.get_stream_type_display())
        
        target_str = f"({', '.join(details)})" if details else "(عام لجميع الصفوف/الشعب/التخصصات)"

        return (
            f"{self.get_exam_type_display()} - {self.subject.name} "
            f"لـ {target_str} ({self.academic_term.name}, {self.academic_year.name}) - {self.exam_date}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.exam_date > datetime.date.today():
            raise ValidationError(
                _("لا يمكن تحديد تاريخ اختبار مستقبلي.")
            )
        if self.total_marks <= 0:
            raise ValidationError(
                _("يجب أن تكون الدرجة الكلية للاختبار أكبر من صفر.")
            )

       
        if self.target_section:
            if not self.target_class:
                self.target_class = self.target_section.class_obj
            elif self.target_class != self.target_section.class_obj:
                raise ValidationError(
                    _("الشعبة المستهدفة يجب أن تنتمي إلى الصف المستهدف المحدد.")
                )
            if self.stream_type:
                raise ValidationError(
                    _("لا يمكن تحديد نوع تخصص للامتحان عند استهداف شعبة محددة. تخصص الشعبة هو المحدد.")
                )
        
       
        elif self.stream_type: 
            if not self.target_class:
                raise ValidationError(
                    _("عند تحديد نوع التخصص (مثل علمي أو أدبي)، يجب تحديد الصف المستهدف.")
                )
        
        # 3. منع تضارب الامتحانات لنفس المادة/التاريخ/النوع/الفصل/العام
        # هذا هو الجزء الأكثر أهمية لضمان التفرد الدقيق
        # يجب أن نتحقق من عدم وجود امتحان آخر يغطي نفس الطلاب لنفس الظروف
        
        # تصفية الامتحانات الأخرى التي قد تتعارض (بنفس المادة، العام، الفصل، النوع، التاريخ)
        conflicting_exams_query = Exam.objects.filter(
            subject=self.subject,
            academic_year=self.academic_year,
            academic_term=self.academic_term,
            exam_type=self.exam_type,
            exam_date=self.exam_date
        )
        # استبعاد الكائن الحالي إذا كان يتم تحريره بدلاً من إنشائه
        if self.pk:
            conflicting_exams_query = conflicting_exams_query.exclude(pk=self.pk)

        # Iterate over potential conflicts
        for existing_exam in conflicting_exams_query:
            # أ. تعارض مع امتحان عام للصف كاملاً (existing_exam يستهدف صفاً فقط)
            if existing_exam.target_class and not existing_exam.target_section and not existing_exam.stream_type:
                # إذا كان الامتحان الجديد يستهدف نفس الصف (كامل، شعبة منه، أو تخصص منه)
                if self.target_class == existing_exam.target_class:
                    if not self.target_section and not self.stream_type: # الجديد عام لنفس الصف
                        raise ValidationError(_(f"يوجد بالفعل امتحان عام للصف {self.target_class.name} في نفس التاريخ ونوع الاختبار."))
                    elif self.target_section and self.target_section.class_obj == existing_exam.target_class: # الجديد لشعبة من نفس الصف
                        raise ValidationError(_(f"يوجد بالفعل امتحان عام للصف {self.target_class.name} يتعارض مع هذا الامتحان لشعبة {self.target_section.name}."))
                    elif self.stream_type and self.target_class == existing_exam.target_class: # الجديد لتخصص من نفس الصف
                        raise ValidationError(_(f"يوجد بالفعل امتحان عام للصف {self.target_class.name} يتعارض مع هذا الامتحان لتخصص {self.get_stream_type_display()}."))

            # ب. تعارض مع امتحان يستهدف شعبة محددة (existing_exam يستهدف شعبة)
            elif existing_exam.target_section:
                # إذا كان الامتحان الجديد يستهدف نفس الشعبة
                if self.target_section == existing_exam.target_section:
                    raise ValidationError(_(f"يوجد بالفعل امتحان للشعبة {self.target_section.name} في نفس التاريخ ونوع الاختبار."))
                # إذا كان الامتحان الجديد يستهدف صفاً كاملاً يتضمن هذه الشعبة
                elif self.target_class == existing_exam.target_section.class_obj and \
                     not self.target_section and not self.stream_type:
                     raise ValidationError(_(f"يوجد امتحان للشعبة {existing_exam.target_section.name} يتعارض مع هذا الامتحان العام لصف {self.target_class.name}."))
                # إذا كان الامتحان الجديد يستهدف تخصصاً يضم هذه الشعبة
                elif self.target_class == existing_exam.target_section.class_obj and \
                     self.stream_type == existing_exam.target_section.stream_type and \
                     not self.target_section:
                     raise ValidationError(_(f"يوجد امتحان للشعبة {existing_exam.target_section.name} يتعارض مع هذا الامتحان لتخصص {self.get_stream_type_display()}."))

            # ج. تعارض مع امتحان يستهدف صف وتخصص معين (existing_exam يستهدف صف وتخصص)
            elif existing_exam.target_class and existing_exam.stream_type:
                # إذا كان الامتحان الجديد يستهدف نفس الصف ونفس التخصص
                if self.target_class == existing_exam.target_class and \
                   self.stream_type == existing_exam.stream_type:
                    raise ValidationError(_(f"يوجد بالفعل امتحان لـ {self.target_class.name} {self.get_stream_type_display()} في نفس التاريخ ونوع الاختبار."))
                # إذا كان الامتحان الجديد يستهدف صفاً كاملاً (ويتضارب مع تخصص منه)
                elif self.target_class == existing_exam.target_class and \
                     not self.target_section and not self.stream_type:
                    raise ValidationError(_(f"يوجد امتحان لـ {existing_exam.target_class.name} {existing_exam.get_stream_type_display()} يتعارض مع هذا الامتحان العام لصف {self.target_class.name}."))
                # إذا كان الامتحان الجديد يستهدف شعبة تنتمي لهذا الصف وهذا التخصص
                elif self.target_section and \
                     self.target_section.class_obj == existing_exam.target_class and \
                     self.target_section.stream_type == existing_exam.stream_type:
                    raise ValidationError(_(f"يوجد امتحان لـ {existing_exam.target_class.name} {existing_exam.get_stream_type_display()} يتعارض مع هذا الامتحان لشعبة {self.target_section.name}."))
        
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
    out_of = models.DecimalField( 
        max_digits=5,
        decimal_places=2,
        verbose_name=_("من أصل"),
        help_text=_("الدرجة القصوى الممكنة التي يمكن الحصول عليها في هذا التقييم.")
    )
    graded_by = models.ForeignKey( 
        User,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        verbose_name=_("تم التقييم بواسطة"),
        related_name='graded_student_scores'
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
        ordering = ['-exam__exam_date', 'student__user__first_name']
        # قيد فريد لضمان درجة واحدة فقط لكل طالب في كل امتحان
        unique_together = [
            ['student', 'exam']
        ]

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} - {self.exam.subject.name} "
            f"{self.exam.get_exam_type_display()} - {self.score}/{self.out_of}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError

        # التحقق من أن الدرجة المحرزة لا تتجاوز الدرجة الكلية للتقييم (out_of)
        if self.score > self.out_of:
            raise ValidationError(
                _("لا يمكن أن تكون الدرجة المحرزة أكبر من الدرجة القصوى لهذا التقييم ({}).").format(self.out_of)
            )

        # التحقق من أن الدرجة المحرزة ليست سالبة
        if self.score < 0:
            raise ValidationError(
                _("لا يمكن أن تكون الدرجة المحرزة سالبة.")
            )
        
        # التحقق من أن out_of أكبر من صفر
        if self.out_of <= 0:
            raise ValidationError(
                _("يجب أن تكون الدرجة القصوى للتقييم (out of) أكبر من صفر.")
            )

        # التحقق من أن graded_at ليس في المستقبل
        if self.graded_at and self.graded_at > datetime.datetime.now():
            raise ValidationError(
                _("لا يمكن تحديد تاريخ ووقت تقييم مستقبلي.")
            )
        
        # لا يوجد تحقق لدور graded_by هنا، حيث ستدير الصلاحيات بالمجموعات.
        # إذا كان Graded_by إلزامياً، يجب إزالة null=True, blank=True منه.
        # وقد ترغب في إضافة هذا التحقق إذا كان graded_by غير إلزامي ولكن يجب أن يكون موجوداً عند الحفظ:
        # if not self.graded_by:
        #     raise ValidationError(_("يجب تحديد المستخدم الذي قام بتسجيل الدرجة."))

        super().clean()
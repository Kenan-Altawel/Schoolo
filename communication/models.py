# academic/models.py
# (تكملة لنفس الملف الذي يحتوي على جميع النماذج الأكاديمية الأخرى)

from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel, User # تأكد من استيراد CustomUser
import datetime # لاستخدام datetime.date أو datetime.datetime
from academic.models import AcademicTerm,AcademicYear
from classes.models import Class, Section # استيراد Class و Section من تطبيق 'classes'
from subject.models import Subject


class NewsActivity(AutoCreateAndAutoUpdateTimeStampedModel):
    NEWS_TYPE_CHOICES = [
        ('announcement', _('إعلان')),
        ('activity', _('نشاط')),
    ]
    TARGET_AUDIENCE_CHOICES = [
        ('all', _('الجميع')),
        ('teachers', _('المعلمون')),  # هذا هو الخيار الذي تختاره
        ('students', _('الطلاب')),  # وهذا أيضاً
        ('class', _('فصل دراسي')),
        ('section', _('قسم')),
        ('subject', _('مادة دراسية')),
    ]


    title = models.CharField(
        max_length=255,
        verbose_name=_("العنوان"),
        help_text=_("عنوان الإعلان أو النشاط.")
    )
    description = models.TextField(
        verbose_name=_("الوصف"),
        help_text=_("وصف تفصيلي للإعلان أو النشاط.")
    )
    created_by = models.ForeignKey(
        User, # من أنشأ هذا الإعلان/النشاط
        on_delete=models.SET_NULL, # لا تحذف الإعلان إذا حذف المستخدم
        null=True,
        blank=True,
        verbose_name=_("تم الإنشاء بواسطة"),
        related_name='created_news_activities'
    )
    type = models.CharField(
        max_length=20,
        choices=NEWS_TYPE_CHOICES,
        default='announcement',
        verbose_name=_("النوع"),
        help_text=_("هل هو إعلان عام أم نشاط محدد؟")
    )

    target_audience = models.CharField(
        max_length=20,
        choices=TARGET_AUDIENCE_CHOICES,
        default='all',
        verbose_name=_("الجمهور المستهدف")
    )
    target_class = models.ForeignKey(
        Class, # هنا نستخدم اسم النموذج مباشرة لأنه تم استيراده
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("الفصل المستهدف"),
        help_text=_("يُحدد إذا كان الجمهور المستهدف 'فصل دراسي'.")
    )
    target_section = models.ForeignKey(
        Section, # هنا نستخدم اسم النموذج مباشرة لأنه تم استيراده
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("القسم المستهدف"),
        help_text=_("يُحدد إذا كان الجمهور المستهدف 'قسم'.")
    )
    target_subject = models.ForeignKey(
        Subject, # هنا نستخدم اسم النموذج مباشرة لأنه تم استيراده
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("المادة المستهدفة"),
        help_text=_("يُحدد إذا كان الجمهور المستهدف 'مادة دراسية'.")
    )
    activity_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("تاريخ النشاط"),
        help_text=_("تاريخ حدوث النشاط (يُستخدم إذا كان النوع 'نشاط').")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='news_activities',
        verbose_name=_("العام الدراسي")
    )
    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='news_activities',
        verbose_name=_("الفصل الدراسي")
    )
    class Meta:
        verbose_name = _("إعلان/نشاط")
        verbose_name_plural = _("الإعلانات والأنشطة")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) - {self.get_target_audience_display()}"

    def clean(self):
        from django.core.exceptions import ValidationError

        # التحقق من حقل 'activity_date' إذا كان النوع 'نشاط'
        if self.type == 'activity' and not self.activity_date:
            raise ValidationError(_("يجب تحديد تاريخ النشاط إذا كان نوع الخبر 'نشاط'."))
        if self.type == 'announcement' and self.activity_date:
            raise ValidationError(_("لا يمكن تحديد تاريخ النشاط إذا كان نوع الخبر 'إعلان'."))

        if self.target_audience == 'class' and not self.target_class:
            raise ValidationError(_("يجب تحديد فصل دراسي مستهدف عندما يكون الجمهور 'فصل دراسي'."))
        if self.target_audience != 'class' and self.target_class:
            raise ValidationError(_("لا يمكن تحديد فصل دراسي مستهدف إلا عندما يكون الجمهور 'فصل دراسي'."))

        if self.target_audience == 'section' and not self.target_section:
            raise ValidationError(_("يجب تحديد قسم مستهدف عندما يكون الجمهور 'قسم'."))
        if self.target_audience != 'section' and self.target_section:
            raise ValidationError(_("لا يمكن تحديد قسم مستهدف إلا عندما يكون الجمهور 'قسم'."))

        if self.target_audience == 'subject' and not self.target_subject:
            raise ValidationError(_("يجب تحديد مادة دراسية مستهدفة عندما يكون الجمهور 'مادة دراسية'."))
        if self.target_audience != 'subject' and self.target_subject:
            raise ValidationError(_("لا يمكن تحديد مادة دراسية مستهدفة إلا عندما يكون الجمهور 'مادة دراسية'."))

        # التأكد من أن حقول target_class, target_section, target_subject فارغة إذا كان الجمهور 'all', 'teachers', 'students'
        if self.target_audience in ['all', 'teachers', 'students']:
            if self.target_class or self.target_section or self.target_subject:
                raise ValidationError(_("لا يمكن تحديد هدف محدد (فصل/قسم/مادة) عندما يكون الجمهور 'الجميع' أو 'معلمون' أو 'طلاب'."))
            
        if self.academic_year and self.academic_term:
            if self.academic_term.academic_year != self.academic_year:
                raise ValidationError(_("الفصل الدراسي المحدد لا ينتمي إلى العام الدراسي المحدد."))

        super().clean()
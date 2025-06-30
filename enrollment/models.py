

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from academic.models import AcademicYear
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel

class RegistrationPeriod(AutoCreateAndAutoUpdateTimeStampedModel):
    id = models.AutoField(primary_key=True)
    academic_year = models.ForeignKey(
        AcademicYear, 
        on_delete=models.CASCADE,
        related_name='registration_periods',
        verbose_name=_("العام الأكاديمي")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("اسم فترة التسجيل"),
        help_text=_("مثال: فترة التسجيل للطلاب الجدد 2025")
    )
    start_date = models.DateField(verbose_name=_("تاريخ بداية فترة التسجيل"))
    end_date = models.DateField(verbose_name=_("تاريخ نهاية فترة التسجيل"))
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("نشطة حالياً؟"),
        help_text=_("هل هذه الفترة نشطة حالياً؟")
    )
    REGISTRATION_TYPE_CHOICES = (
        ('new_students', _('طلاب جدد')),
        ('returning_students', _('طلاب عائدون')),
        ('all', _('الكل')),
    )
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        verbose_name=_("نوع التسجيل"),
        help_text=_("لتحديد نوع التسجيل (طلاب جدد/عائدون/الكل)")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_registration_periods',
        verbose_name=_("أنشأ بواسطة")
    )
    # حقول created_at و updated_at تم توريثها من AutoCreateAndAutoUpdateTimeStampedModel

    class Meta(AutoCreateAndAutoUpdateTimeStampedModel.Meta): # توريث الـ Meta أيضاً أو تعريفها من جديد
        verbose_name = _("فترة تسجيل")
        verbose_name_plural = _("فترات التسجيل")
        ordering = ['-start_date'] # ترتيب افتراضي حسب تاريخ البداية تنازليًا

    def __str__(self):
        return self.name

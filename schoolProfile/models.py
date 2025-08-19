from django.db import models
from django.utils.translation import gettext_lazy as _

class SchoolProfile(models.Model):
    class SchoolType(models.TextChoices):
        PRIMARY = 'Primary', _('ابتدائي')
        MIDDLE = 'Middle', _('إعدادي')
        SECONDARY = 'Secondary', _('ثانوي')

    class SchoolStatus(models.TextChoices):
        PUBLIC = 'Public', _('حكومي')
        PRIVATE = 'Private', _('خاصة')

    school_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('اسم المدرسة'))
    school_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('هاتف المدرسة'))
    school_logo = models.ImageField(upload_to='schoolProfile/logo/', blank=True, null=True, verbose_name=_('شعار المدرسة'))
    email = models.EmailField(blank=True, null=True, verbose_name=_('البريد الإلكتروني'))
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('العنوان'))
    school_type = models.CharField(max_length=20, choices=SchoolType.choices, blank=True, null=True, verbose_name=_('نوع المدرسة'))
    school_status = models.CharField(max_length=20, choices=SchoolStatus.choices, blank=True, null=True, verbose_name=_('حالة المدرسة'))

    class Meta:
        verbose_name = _('ملف المدرسة')
        verbose_name_plural = _('ملف المدرسة')

    def __str__(self):
        return self.school_name or _('ملف المدرسة') 
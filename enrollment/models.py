from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

class RegistrationSetting(models.Model):
    """
    نموذج singleton (أحادي) لتحديد ما إذا كان التسجيل مفتوحًا عالميًا أم مغلقًا.
    يجب أن يحتوي على سجل واحد فقط في قاعدة البيانات.
    """
    is_registration_open = models.BooleanField(
        default=False,
        verbose_name=_("هل التسجيل مفتوح حالياً؟"),
        help_text=_("التحكم العام في فتح أو إغلاق التسجيل للمدرسة بأكملها.")
    )

    class Meta:
        verbose_name = _("إعداد التسجيل العام")
        verbose_name_plural = _("إعدادات التسجيل العام")

    def __str__(self):
        return _("التسجيل مفتوح: {}").format(_("نعم") if self.is_registration_open else _("لا"))

    def save(self, *args, **kwargs):
        if RegistrationSetting.objects.exists() and not self.pk:
            raise ValidationError(_("يجب أن يكون هناك سجل واحد فقط لإعدادات التسجيل العالمية. الرجاء تعديل السجل الحالي بدلاً من إنشاء سجل جديد."))
        super().save(*args, **kwargs)



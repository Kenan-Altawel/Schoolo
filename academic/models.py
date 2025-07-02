from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel # استيراد النموذج المساعد
import datetime

class AcademicYear(AutoCreateAndAutoUpdateTimeStampedModel):
    name = models.CharField(max_length=50,unique=True,verbose_name=_("اسم العام الدراسي"))
    start_date = models.DateField(verbose_name=_("تاريخ البدء"))
    end_date = models.DateField(verbose_name=_("تاريخ الانتهاء"))
    is_current = models.BooleanField(default=False,verbose_name=_("هل هو العام الحالي؟"))

    class Meta:
        verbose_name = _("عام دراسي")
        verbose_name_plural = _("سنوات دراسية")
        ordering = ['-start_date'] 

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs) 


class AcademicTerm(AutoCreateAndAutoUpdateTimeStampedModel):
    academic_year = models.ForeignKey(AcademicYear,on_delete=models.CASCADE,related_name='academic_terms')
    name = models.CharField(max_length=100,verbose_name=_("اسم الفصل الدراسي"),)
    start_date = models.DateField(verbose_name=_("تاريخ البدء"))
    end_date = models.DateField(verbose_name=_("تاريخ الانتهاء"))
    is_current = models.BooleanField(default=False,verbose_name=_("هل هو الفصل الحالي؟"))

    class Meta:
        verbose_name = _("فصل دراسي")
        verbose_name_plural = _("فصول دراسية")
        unique_together = [['academic_year', 'name']] # يضمن فرادة اسم الفصل داخل العام الدراسي الواحد
        ordering = ['-academic_year__start_date', 'start_date'] # ترتيب حسب العام ثم تاريخ بدء الفصل

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"

    def save(self, *args, **kwargs):
        if self.is_current:
            
            AcademicTerm.objects.filter(
                academic_year=self.academic_year, # في نفس العام الدراسي
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class TimeSlot(models.Model):
    slot_number = models.IntegerField(unique=True, help_text=_('الترتيب التسلسلي للحصة/الفترة في اليوم (مثال: 1, 2, 3...)'))
    start_time = models.TimeField(help_text=_('وقت بدء الفترة الزمنية (مثال: 08:00)'))
    end_time = models.TimeField(help_text=_('وقت انتهاء الفترة الزمنية (مثال: 08:45)'))
    is_break = models.BooleanField(default=False, help_text=_('هل هذه الفترة استراحة وليست حصة دراسية؟'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['slot_number']
        verbose_name = _("الفترة الزمنية للحصة") 
        verbose_name_plural = _("الفترات الزمنية للحصص") 

    def __str__(self):
       
        return f"Slot {self.slot_number}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class DayOfWeek(models.Model):
    id = models.IntegerField(primary_key=True, help_text=_('1=الأحد, 2=الاثنين, ..., 7=السبت'))
    name_ar = models.CharField(max_length=20, unique=True, help_text=_('اسم اليوم  (مثال: الأحد)'))
    is_school_day = models.BooleanField(default=True, help_text=_('هل هذا اليوم يوم دراسي عادي؟ (للسماح بالعطلات)'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = _("يوم الأسبوع") 
        verbose_name_plural = _("أيام الأسبوع") 

    def __str__(self):
        return self.name_ar

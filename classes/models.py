from django.db import models
import datetime
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel, User
from django.utils.translation import gettext_lazy as _
from academic.models import AcademicYear
class Class(AutoCreateAndAutoUpdateTimeStampedModel):
    name = models.CharField(max_length=100,verbose_name=_("اسم الفصل"),)
    description = models.TextField(blank=True,null=True,verbose_name=_("الوصف"))

    class Meta:
        verbose_name = _("الفصل الدراسي")
        verbose_name_plural = _("الفصول الدراسية")
        unique_together = ['name'] # يضمن فرادة اسم الفصل داخل العام الدراسي الواحد
        ordering = [ 'name'] # ترتيب حسب العام الدراسي ثم اسم الفصل

    def __str__(self):
        return f"{self.name} "
    

class Section(AutoCreateAndAutoUpdateTimeStampedModel):
    STREAM_TYPE_CHOICES = [
        ('General', _('عام')),
        ('Scientific', _('علمي')),
        ('Literary', _('أدبي')),
        
    ]

    name = models.CharField(max_length=100, verbose_name=_("اسم الشعبة")) 
    stream_type = models.CharField(max_length=50,choices=STREAM_TYPE_CHOICES,blank=True,help_text=_("مثل: علمي، أدبي، عام."))
    academic_year = models.ForeignKey(AcademicYear,on_delete=models.CASCADE,related_name='sections_by_year', verbose_name=_("العام الدراسي"))
    class_obj = models.ForeignKey('Class',on_delete=models.CASCADE,related_name='sections',verbose_name=_("الفصل الدراسي"))
    capacity = models.IntegerField(null=True,blank=True,verbose_name=_("السعة القصوى للقسم"),help_text=_("الحد الأقصى لعدد الطلاب في هذا القسم."))
    is_active = models.BooleanField(default=False,verbose_name=_("هل القسم نشط؟"),help_text=_("يشير إلى ما إذا كان القسم قيد الاستخدام حاليًا."))
    activation_date = models.DateTimeField(null=True,blank=True,verbose_name=_("تاريخ التفعيل"))
    deactivation_date = models.DateTimeField(null=True,blank=True,verbose_name=_("تاريخ إلغاء التفعيل"))

    class Meta:
        verbose_name = _("القسم")
        verbose_name_plural = _("الأقسام")
        unique_together = [['name', 'academic_year', 'class_obj']]
        ordering = ['academic_year__name', 'class_obj__name', 'name']
       

    def __str__(self):
        return f"{self.name} - {self.class_obj.name} ({self.academic_year.name})"

    def save(self, *args, **kwargs):
        if self.is_active and not self.activation_date:
            self.activation_date = datetime.datetime.now()
            self.deactivation_date = None 
        elif not self.is_active and not self.deactivation_date and self.pk:
            self.deactivation_date = datetime.datetime.now()
        
        super().save(*args, **kwargs)


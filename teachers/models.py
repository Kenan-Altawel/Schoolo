from django.db import models
from django.utils.translation import gettext_lazy as _
from academic.models import DayOfWeek
from accounts.models import User, AutoCreateAndAutoUpdateTimeStampedModel

class Teacher(AutoCreateAndAutoUpdateTimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='teacher_profile', 
        verbose_name=_("المستخدم المرتبط")
    )
    address = models.TextField( 
        blank=True,
        null=True,
        verbose_name=_("العنوان")
    )
    specialization = models.CharField(
        max_length=255, 
        blank=True,
        null=True,
        verbose_name=_("التخصص")
    )
    class Meta:
        verbose_name = _("المعلم")
        verbose_name_plural = _("المعلمون")
        ordering = ['user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.phone_number
    

class TeacherAvailability(AutoCreateAndAutoUpdateTimeStampedModel):

    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE,
        related_name='availability',
        verbose_name=_("المعلم")
    )
    day_of_week = models.ForeignKey(DayOfWeek,on_delete=models.CASCADE,related_name='teacher_availability',verbose_name=_("يوم الأسبوع"))

    class Meta:
        verbose_name = _("توفر المعلم")
        verbose_name_plural = _("توفر المعلمين")
        unique_together = [
            ['teacher', 'day_of_week']
        ]
        ordering = ['teacher__user__first_name', 'day_of_week']

    def __str__(self):
        return (
            f"{self.teacher.user.get_full_name()} متاح يوم {self.day_of_week.name_ar}"
        )

    
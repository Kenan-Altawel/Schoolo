
from django.db import models
from django.utils.translation import gettext_lazy as _
from academic.models import AcademicTerm, AcademicYear
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel, User
from students.models import Student 
import datetime 

class Attendance(AutoCreateAndAutoUpdateTimeStampedModel):
    ATTENDANCE_STATUS_CHOICES = [
        ('present', _('حاضر')),
        ('absent', _('غائب')),
        ('late', _('متأخر')),
        ('excused', _('معذور')),
        
    ]

    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='attendances',
        verbose_name=_("الطالب")
    )
    date = models.DateField(
        verbose_name=_("التاريخ"),
        help_text=_("تاريخ تسجيل الحضور.")
    )
    status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='present',
        verbose_name=_("الحالة"),
        help_text=_("حالة حضور الطالب: حاضر، غائب، متأخر، معذور.")
    )
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        verbose_name=_("تم التسجيل بواسطة"),
        related_name='recorded_attendances'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        verbose_name=_("العام الدراسي")
    )
    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        verbose_name=_("الفصل الدراسي")
    )

    class Meta:
        verbose_name = _("سجل حضور")
        verbose_name_plural = _("سجلات الحضور")
        ordering = ['-date', 'student__user__first_name']
        unique_together = [
            ['student', 'date', 'academic_term','academic_year'] 
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date} - {self.get_status_display()}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.date > datetime.date.today():
            raise ValidationError(
                _("لا يمكن تسجيل الحضور لتاريخ مستقبلي.")
            )

        super().clean()
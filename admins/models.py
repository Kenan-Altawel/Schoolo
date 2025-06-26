from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User, AutoCreateAndAutoUpdateTimeStampedModel

class Admin(AutoCreateAndAutoUpdateTimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True, 
        related_name='admin_profile', 
        verbose_name=_("المستخدم المرتبط")
    )
    department = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("القسم")
    )

    class Meta:
        verbose_name = _("المسؤول")
        verbose_name_plural = _("المسؤولون")
        ordering = ['user__first_name', 'user__last_name'] # ترتيب المسؤولين بالاسم

    def __str__(self):
        return self.user.get_full_name() or self.user.phone_number
    
    

    def __str__(self):
        return self.username
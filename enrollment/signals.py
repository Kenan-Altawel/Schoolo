
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .models import RegistrationSetting 
from django.contrib.auth.models import Group


@receiver(post_migrate)
def create_initial_settings_and_groups(sender, app_config, **kwargs):
    if app_config.label == 'accounts': 
        print(_("loading ....."))

        setting, created = RegistrationSetting.objects.get_or_create(pk=1)
        if created:
            print(_("تم إنشاء سجل إعدادات التسجيل العامة الافتراضي."))
        


from django.apps import AppConfig


class EnrollmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enrollment'
    verbose_name = "إعدادات المدرسة"

    def ready(self):
       import enrollment.signals


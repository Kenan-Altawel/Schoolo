from django.apps import AppConfig


class AcademicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academic'

    def ready(self):
        # استيراد signals عند جاهزية التطبيق
        import academic.signals
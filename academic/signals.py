
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import DayOfWeek

@receiver(post_migrate)
def create_default_days_of_week(sender, **kwargs):
    # تحقق من أن signals يعمل للتطبيق الصحيح
    if sender.label != 'academic':
        return
    
    # قائمة الأيام التي سيتم إضافتها
    days = [
        {'id': 1, 'name_ar': 'الاثنين',  'is_school_day': True},
        {'id': 2, 'name_ar': 'الثلاثاء',  'is_school_day': True},
        {'id': 3, 'name_ar': 'الأربعاء',  'is_school_day': True},
        {'id': 4, 'name_ar': 'الخميس',  'is_school_day': True},
        {'id': 5, 'name_ar': 'الجمعة', 'is_school_day': True},
        {'id': 6, 'name_ar': 'السبت',  'is_school_day': False},
        {'id': 7, 'name_ar': 'الأحد',  'is_school_day': False},
    ]

    for day_data in days:
        DayOfWeek.objects.get_or_create(id=day_data['id'], defaults=day_data)
    
    print("days of week created successfully")
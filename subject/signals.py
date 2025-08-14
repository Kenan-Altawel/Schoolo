# subject/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import SubjectIcon


@receiver(post_migrate)
def create_initial_subject_icons(sender, **kwargs):
    # للتأكد من أن الـ signal يعمل للتطبيق الصحيح
    if sender.label != 'subject':
        return

    # قائمة الأيقونات الثابتة التي سيتم إضافتها
    icons_to_create = [
        {'name': 'رياضيات', 'icon_file': 'subject/subject_files/icons/math.png'},
        {'name': 'كيمياء', 'icon_file': 'subject/subject_files/icons/chemistry.png'},
    ]

    for icon_data in icons_to_create:
        SubjectIcon.objects.get_or_create(
            name=icon_data['name'], 
            defaults=icon_data
        )

    print("Initial subject icons created successfully!")
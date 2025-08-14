# students/signals/handlers.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ..models import Student
from classes.models import Section

@receiver(post_save, sender=Student)
def update_section_count_on_save(sender, instance, created, **kwargs):
    # تحديث عدد الطلاب عند إضافة أو تعديل طالب
    # if the student section is not null
    if instance.section:
        instance.section.students_count = instance.section.students.count()
        instance.section.save()

@receiver(post_delete, sender=Student)
def update_section_count_on_delete(sender, instance, **kwargs):
    # تحديث عدد الطلاب عند حذف طالب
    if instance.section:
        instance.section.students_count = instance.section.students.count()
        instance.section.save()
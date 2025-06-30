
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group

def create_default_groups(sender, **kwargs):
    if sender.label != 'accounts':
        return

    student_group, created = Group.objects.get_or_create(name='Student')
    if created:
        print("student")
    teacher_group, created = Group.objects.get_or_create(name='Teacher')
    if created:
        print("tescher")

    manager_group, created = Group.objects.get_or_create(name='Manager')
    if created:
        print("manager")


post_migrate.connect(create_default_groups)
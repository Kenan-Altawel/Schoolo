# Generated by Django 5.2.1 on 2025-06-17 16:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academic', '0001_initial'),
        ('classes', '0001_initial'),
        ('subject', '0001_initial'),
        ('teachers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ آخر تحديث')),
                ('day_of_week', models.CharField(choices=[('Monday', 'الاثنين'), ('Tuesday', 'الثلاثاء'), ('Wednesday', 'الأربعاء'), ('Thursday', 'الخميس'), ('Friday', 'الجمعة'), ('Saturday', 'السبت'), ('Sunday', 'الأحد')], help_text='اليوم الذي ستقام فيه الحصة.', max_length=10, verbose_name='يوم الأسبوع')),
                ('period', models.CharField(help_text="توقيت الحصة أو رقم الفترة (مثال: '08:00-09:00' أو 'الفترة الأولى').", max_length=50, verbose_name='الفترة/الحصة')),
                ('academic_term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_schedules', to='academic.academicterm', verbose_name='الفصل الدراسي')),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_schedules', to='academic.academicyear', verbose_name='العام الدراسي')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_schedules', to='classes.section', verbose_name='القسم')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_schedules', to='subject.subject', verbose_name='المادة الدراسية')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teaching_schedules', to='teachers.teacher', verbose_name='المعلم')),
            ],
            options={
                'verbose_name': 'جدول حصص معتمد',
                'verbose_name_plural': 'جداول الحصص المعتمدة',
                'ordering': ['academic_year', 'academic_term', 'section', 'day_of_week', 'period'],
                'unique_together': {('subject', 'section', 'academic_year', 'academic_term', 'day_of_week', 'period')},
            },
        ),
        migrations.CreateModel(
            name='ProposedClassSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ آخر تحديث')),
                ('day_of_week', models.CharField(choices=[('Monday', 'الاثنين'), ('Tuesday', 'الثلاثاء'), ('Wednesday', 'الأربعاء'), ('Thursday', 'الخميس'), ('Friday', 'الجمعة'), ('Saturday', 'السبت'), ('Sunday', 'الأحد')], help_text='اليوم الذي ستقام فيه الحصة.', max_length=10, verbose_name='يوم الأسبوع')),
                ('period', models.CharField(help_text="توقيت الحصة أو رقم الفترة (مثال: '08:00-09:00' أو 'الفترة الأولى').", max_length=50, verbose_name='الفترة/الحصة')),
                ('status', models.CharField(choices=[('proposed', 'مقترح'), ('accepted', 'مقبول'), ('rejected', 'مرفوض')], default='proposed', help_text='حالة المقترح: مقترح، مقبول، مرفوض.', max_length=10, verbose_name='الحالة')),
                ('academic_term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposed_schedules', to='academic.academicterm', verbose_name='الفصل الدراسي')),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposed_schedules', to='academic.academicyear', verbose_name='العام الدراسي')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposed_schedules', to='classes.section', verbose_name='القسم')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposed_schedules', to='subject.subject', verbose_name='المادة الدراسية')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='proposed_teaching_schedules', to='teachers.teacher', verbose_name='المعلم')),
            ],
            options={
                'verbose_name': 'جدول حصص مقترح',
                'verbose_name_plural': 'جداول الحصص المقترحة',
                'ordering': ['academic_year', 'academic_term', 'section', 'day_of_week', 'period'],
                'unique_together': {('subject', 'section', 'academic_year', 'academic_term', 'day_of_week', 'period')},
            },
        ),
    ]

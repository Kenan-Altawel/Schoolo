# Generated by Django 5.2.1 on 2025-06-17 16:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academic', '0001_initial'),
        ('classes', '0001_initial'),
        ('students', '0001_initial'),
        ('subject', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ آخر تحديث')),
                ('exam_type', models.CharField(choices=[('midterm', 'اختبار منتصف الفصل'), ('final', 'اختبار نهائي'), ('quiz', 'اختبار قصير'), ('assignment', 'واجب')], help_text='نوع الاختبار أو التقييم (مثال: اختبار نصفي، واجب، نهائي).', max_length=20, verbose_name='نوع الاختبار')),
                ('exam_date', models.DateField(help_text='التاريخ الذي أقيم فيه الاختبار.', verbose_name='تاريخ الاختبار')),
                ('total_marks', models.DecimalField(decimal_places=2, help_text='الدرجة الكلية الممكنة لهذا الاختبار.', max_digits=5, verbose_name='الدرجة الكلية')),
                ('stream_type', models.CharField(blank=True, choices=[('scientific', 'علمي'), ('literary', 'أدبي'), ('general', 'عام')], help_text='نوع التخصص المستهدف (مثال: علمي، أدبي) ضمن الصف المحدد.', max_length=20, null=True, verbose_name='نوع التخصص')),
                ('academic_term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='academic.academicterm', verbose_name='الفصل الدراسي')),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='academic.academicyear', verbose_name='العام الدراسي')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='subject.subject', verbose_name='المادة الدراسية')),
                ('target_class', models.ForeignKey(blank=True, help_text='الصف الذي يستهدفه هذا الاختبار (إذا لم يكن لجميع الصفوف).', null=True, on_delete=django.db.models.deletion.SET_NULL, to='classes.class', verbose_name='الصف المستهدف')),
                ('target_section', models.ForeignKey(blank=True, help_text='الشعبة المحددة داخل الصف المستهدف.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='classes.section', verbose_name='الشعبة المستهدفة')),
            ],
            options={
                'verbose_name': 'اختبار',
                'verbose_name_plural': 'الاختبارات',
                'ordering': ['-exam_date', 'subject__name'],
                'unique_together': {('subject', 'academic_year', 'academic_term', 'exam_type', 'exam_date', 'target_class', 'target_section', 'stream_type')},
            },
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ آخر تحديث')),
                ('score', models.DecimalField(decimal_places=2, help_text='الدرجة التي حصل عليها الطالب في هذا الاختبار.', max_digits=5, verbose_name='الدرجة المحرزة')),
                ('out_of', models.DecimalField(decimal_places=2, help_text='الدرجة القصوى الممكنة التي يمكن الحصول عليها في هذا التقييم.', max_digits=5, verbose_name='من أصل')),
                ('graded_at', models.DateTimeField(blank=True, help_text='التاريخ والوقت الذي تم فيه تسجيل الدرجة.', null=True, verbose_name='تاريخ ووقت التقييم')),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='grading.exam', verbose_name='الاختبار')),
                ('graded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='graded_student_scores', to=settings.AUTH_USER_MODEL, verbose_name='تم التقييم بواسطة')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='students.student', verbose_name='الطالب')),
            ],
            options={
                'verbose_name': 'درجة',
                'verbose_name_plural': 'الدرجات',
                'ordering': ['-exam__exam_date', 'student__user__first_name'],
                'unique_together': {('student', 'exam')},
            },
        ),
    ]

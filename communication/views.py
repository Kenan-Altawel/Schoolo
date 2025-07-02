# communication/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .models import NewsActivity
from .serializers import NewsActivitySerializer
from django.db.models import Q
from accounts.models import User
from django.contrib.auth.models import Group # استيراد Group model (مهم جداً لتحديد الأدوار)

class NewsActivityViewSet(viewsets.ModelViewSet):
    serializer_class = NewsActivitySerializer
    # الـ queryset الأساسي الذي سيتم فلترته
    queryset = NewsActivity.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # عند إنشاء إعلان جديد، المبدع هو المستخدم الحالي
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        # ابدأ من الـ queryset الأساسي المحدد في الكلاس
        base_queryset = self.queryset
        user = self.request.user

        # 1. منطق السوبر يوزر: يرى كل شيء
        if user.is_superuser:
            print(f"User '{user.username}' is Superuser. Returning all news activities.")
            return base_queryset

        # 2. تحديد أسماء المجموعات (تأكد أن هذه الأسماء مطابقة تماماً لأسماء المجموعات في Django Admin)
        TEACHERS_GROUP_NAME = "Teachers"
        STUDENTS_GROUP_NAME = "Students"
        # إذا كان لديك مجموعة للـ "Admin" وتريدهم أن يروا كل شيء أيضاً، أضفها هنا
        # ADMINS_GROUP_NAME = "Admins"

        # 3. التحقق من دور المستخدم بناءً على المجموعات
        is_teacher_role = user.groups.filter(name=TEACHERS_GROUP_NAME).exists()
        is_student_role = user.groups.filter(name=STUDENTS_GROUP_NAME).exists()
        # is_admin_role = user.groups.filter(name=ADMINS_GROUP_NAME).exists() # إذا أضفت مجموعة Admin

        # 4. تهيئة شروط التصفية: الجميع يرى الإعلانات العامة تلقائياً
        filter_conditions = Q(target_audience='all')

        # 5. إضافة شروط بناءً على دور المستخدم
        if is_teacher_role:
            print(f"User '{user.username}' is a teacher (by group). Applying teacher-specific filters.")
            # المعلمون يرون الإعلانات الموجهة لمجموعة المعلمين
            filter_conditions |= Q(target_audience='teachers')

            # المعلمون يرون الإعلانات الموجهة للفصول/الأقسام/المواد التي يدرسونها
            # (هذا الجزء يعتمد على وجود الحقول والعلاقات التي ذكرتها سابقاً في User model)
            if hasattr(user, 'classes_taught') and user.classes_taught.exists():
                class_ids = user.classes_taught.values_list('id', flat=True)
                filter_conditions |= Q(target_audience='class', target_class__in=class_ids)

            if hasattr(user, 'sections_taught') and user.sections_taught.exists():
                section_ids = user.sections_taught.values_list('id', flat=True)
                filter_conditions |= Q(target_audience='section', target_section__in=section_ids)

            if hasattr(user, 'subjects_taught') and user.subjects_taught.exists():
                subject_ids = user.subjects_taught.values_list('id', flat=True)
                filter_conditions |= Q(target_audience='subject', target_subject__in=subject_ids)

        elif is_student_role:
            print(f"User '{user.username}' is a student (by group). Applying student-specific filters.")
            # الطلاب يرون الإعلانات الموجهة لمجموعة الطلاب
            filter_conditions |= Q(target_audience='students')

            # الطلاب يرون الإعلانات الموجهة لفصولهم/أقسامهم/موادهم
            # (هذا الجزء يعتمد على وجود الحقول والعلاقات التي ذكرتها سابقاً في User model)
            if hasattr(user, 'current_class') and user.current_class:
                filter_conditions |= Q(target_audience='class', target_class=user.current_class)

            if hasattr(user, 'current_section') and user.current_section:
                filter_conditions |= Q(target_audience='section', target_section=user.current_section)

            if hasattr(user, 'enrolled_subjects') and user.enrolled_subjects.exists():
                subject_ids = user.enrolled_subjects.values_list('id', flat=True)
                filter_conditions |= Q(target_audience='subject', target_subject__in=subject_ids)

        # 6. تطبيق شروط التصفية النهائية على الـ queryset الأساسي
        # .distinct() لضمان عدم تكرار الأنشطة إذا كانت تنطبق عليها أكثر من شرط
        return base_queryset.filter(filter_conditions).distinct()
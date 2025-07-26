# communication/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .models import NewsActivity
from .serializers import NewsActivitySerializer
from django.db.models import Q
from accounts.models import User
from accounts.permissions import *
from django.contrib.auth.models import Group 

class CustomPermission(permissions.BasePermission):
   
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True
        
        else:
            return IsAdminOrSuperuser().has_permission(request, view)

class NewsActivityViewSet(viewsets.ModelViewSet):
    serializer_class = NewsActivitySerializer
    queryset = NewsActivity.objects.all().order_by('-created_at')
    permission_classes = [CustomPermission]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        base_queryset = self.queryset
        user = self.request.user

        queryset_to_filter = base_queryset

        if user.is_superuser or user.is_admin():
            
            # تطبيق الفلترة حسب الجمهور المستهدف (target_audience) إذا تم توفيرها
            target_audience_param = self.request.query_params.get('target_audience', None)
            if target_audience_param:
                queryset_to_filter = queryset_to_filter.filter(target_audience=target_audience_param)

            # تطبيق الفلترة حسب النوع (type) إذا تم توفيرها
            news_type_param = self.request.query_params.get('type', None)
            if news_type_param:
                queryset_to_filter = queryset_to_filter.filter(type=news_type_param)
            
            # تطبيق فلاتر target_class, target_section, target_subject للمدراء
            target_class_id = self.request.query_params.get('target_class_id', None)
            if target_class_id:
                queryset_to_filter = queryset_to_filter.filter(target_class__id=target_class_id)

            target_section_id = self.request.query_params.get('target_section_id', None)
            if target_section_id:
                queryset_to_filter = queryset_to_filter.filter(target_section__id=target_section_id)

            target_subject_id = self.request.query_params.get('target_subject_id', None)
            if target_subject_id:
                queryset_to_filter = queryset_to_filter.filter(target_subject__id=target_subject_id)

            return queryset_to_filter.distinct()

        # 2. للمستخدمين الموثقين الآخرين (المعلمين والطلاب):
        # هنا نبدأ بشروط التصفية الأساسية لكل دور
        filter_conditions = Q(target_audience='all') # الجميع يرى الإعلانات العامة تلقائياً

        is_teacher_role = user.is_teacher() 
        is_student_role = user.is_student() 

        if is_teacher_role:
            print(f"User '{user.username}' is a teacher. Applying teacher-specific filters.")
            filter_conditions |= Q(target_audience='teachers')

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
            print(f"User '{user.username}' is a student. Applying student-specific filters.")
            filter_conditions |= Q(target_audience='students')

            if hasattr(user, 'current_class') and user.current_class:
                filter_conditions |= Q(target_audience='class', target_class=user.current_class)

            if hasattr(user, 'current_section') and user.current_section:
                filter_conditions |= Q(target_audience='section', target_section=user.current_section)

            if hasattr(user, 'enrolled_subjects') and user.enrolled_subjects.exists():
                subject_ids = user.enrolled_subjects.values_list('id', flat=True)
                filter_conditions |= Q(target_audience='subject', target_subject__in=subject_ids)
        
        # 4. تطبيق شروط التصفية الأساسية الخاصة بالدور أولاً
        queryset_to_filter = queryset_to_filter.filter(filter_conditions)

        news_type_param = self.request.query_params.get('type', None)
        if news_type_param:
            queryset_to_filter = queryset_to_filter.filter(type=news_type_param)

        target_class_id = self.request.query_params.get('target_class_id', None)
        if target_class_id:
             queryset_to_filter = queryset_to_filter.filter(target_class__id=target_class_id)

        target_section_id = self.request.query_params.get('target_section_id', None)
        if target_section_id:
             queryset_to_filter = queryset_to_filter.filter(target_section__id=target_section_id)

        target_subject_id = self.request.query_params.get('target_subject_id', None)
        if target_subject_id:
             queryset_to_filter = queryset_to_filter.filter(target_subject__id=target_subject_id)


        return queryset_to_filter.distinct()
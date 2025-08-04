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
from academic.models import AcademicYear, AcademicTerm



class NewsActivityViewSet(viewsets.ModelViewSet):
    serializer_class = NewsActivitySerializer
    queryset = NewsActivity.objects.all().order_by('-created_at')
    permission_classes = [CustomPermission]

    def perform_create(self, serializer):
        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            raise ValueError(_("لا يوجد عام دراسي نشط حالياً لإنشاء الإعلان/النشاط."))
        
        try:
            current_academic_term = AcademicTerm.objects.get(is_current=True, academic_year=current_academic_year)
        except AcademicTerm.DoesNotExist:
            raise ValueError(_("لا يوجد فصل دراسي نشط حالياً ضمن العام الدراسي النشط لإنشاء الإعلان/النشاط."))
            
        serializer.save(
            created_by=self.request.user,
            academic_year=current_academic_year,
            academic_term=current_academic_term
        )
    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if not user.is_authenticated:
            return NewsActivity.objects.none()

        # جلب العام والفصل الدراسي الحاليين
        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            current_academic_year = None
        
        try:
            current_academic_term = AcademicTerm.objects.get(is_current=True, academic_year=current_academic_year)
        except AcademicTerm.DoesNotExist:
            current_academic_term = None

        # منطق المسؤول والمشرف:
        if user.is_superuser or user.is_admin():
            # يمكن للمسؤول رؤية كل شيء وتصفية حسب أي حقل
            return self._apply_common_filters(queryset, current_academic_year, current_academic_term).distinct()

        # منطق المستخدمين الموثقين الآخرين (المعلمين والطلاب):
        filter_conditions = Q(target_audience='all')

        is_teacher_role = user.is_teacher()
        is_student_role = user.is_student()

        if is_teacher_role:
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
            filter_conditions |= Q(target_audience='students')
            if hasattr(user, 'student') and hasattr(user.student, 'current_class') and user.student.current_class:
                filter_conditions |= Q(target_audience='class', target_class=user.student.current_class)
            if hasattr(user, 'student') and hasattr(user.student, 'current_section') and user.student.current_section:
                filter_conditions |= Q(target_audience='section', target_section=user.student.current_section)
            if hasattr(user, 'student') and hasattr(user.student, 'enrolled_subjects') and user.student.enrolled_subjects.exists():
                subject_ids = user.student.enrolled_subjects.values_list('id', flat=True)
                filter_conditions |= Q(target_audience='subject', target_subject__in=subject_ids)

        queryset = queryset.filter(filter_conditions)

        return self._apply_common_filters(queryset, current_academic_year, current_academic_term).distinct()


    def _apply_common_filters(self, queryset, current_academic_year=None, current_academic_term=None):
        """
        دالة مساعدة لتطبيق فلاتر الاستعلام الشائعة (التي يمكن أن يستخدمها الجميع أو المدراء).
        """
        target_audience_param = self.request.query_params.get('target_audience', None)
        news_type_param = self.request.query_params.get('type', None)
        target_class_id = self.request.query_params.get('target_class_id', None)
        target_section_id = self.request.query_params.get('target_section_id', None)
        target_subject_id = self.request.query_params.get('target_subject_id', None)

        academic_year_id_param = self.request.query_params.get('academic_year_id', None)
        academic_term_id_param = self.request.query_params.get('academic_term_id', None)

        # إذا طلب المستخدم عاماً دراسياً محدداً (فقط للمدراء أو Superusers)
        if academic_year_id_param and (self.request.user.is_superuser or self.request.user.is_admin()):
            queryset = queryset.filter(academic_year_id=academic_year_id_param)
        # وإلا، استخدم العام الدراسي الحالي افتراضياً
        elif current_academic_year: # هذا سيطبق على الجميع، بما في ذلك المدراء إذا لم يحددوا عاماً
            queryset = queryset.filter(academic_year=current_academic_year)


        # إذا طلب المستخدم فصلاً دراسياً محدداً (فقط للمدراء أو Superusers)
        if academic_term_id_param and (self.request.user.is_superuser or self.request.user.is_admin()):
            queryset = queryset.filter(academic_term_id=academic_term_id_param)
        # وإلا، استخدم الفصل الدراسي الحالي افتراضياً
        elif current_academic_term: # هذا سيطبق على الجميع، بما في ذلك المدراء إذا لم يحددوا فصلاً
            queryset = queryset.filter(academic_term=current_academic_term)
        
        # الفلاتر الأخرى تبقى كما هي
        if target_audience_param:
            queryset = queryset.filter(target_audience=target_audience_param)
        if news_type_param:
            queryset = queryset.filter(type=news_type_param)
        if target_class_id:
            queryset = queryset.filter(target_class__id=target_class_id)
        if target_section_id:
            queryset = queryset.filter(target_section__id=target_section_id)
        if target_subject_id:
            queryset = queryset.filter(target_subject__id=target_subject_id)

        return queryset
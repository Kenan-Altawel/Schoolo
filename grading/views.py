# exams/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import permissions # يجب استيراد permissions
from django.utils.translation import gettext_lazy as _
from accounts.permissions import *
from .serializers import ExamSerializer
from .models import Exam
from accounts.models import User 
from teachers.models import Teacher
from students.models import Student 
from classes.models import Section # لإمكانية الوصول إلى stream_type من Section في منطق الطالب

# تعريف صلاحية الكتابة (مدير أو معلم)
class IsAuthenticatedAndAdminForWrites(permissions.BasePermission):
    message = _('يجب أن تكون مسجلاً للدخول (authenticated) للوصول إلى هذا المحتوى. يجب أن تكون مديراً أو معلماً لإنشاء أو تعديل الاختبارات.')

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True
        
        else:
            return IsAdminOrSuperuser().has_permission(request, view)

class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticatedAndAdminForWrites]
    queryset = Exam.objects.all() # queryset الأساسي، سيتم فلترته في get_queryset

    def get_queryset(self):
        queryset = super().get_queryset() # ابدأ بالـ queryset الأساسي
        user = self.request.user

        if not user.is_authenticated:
            return Exam.objects.none()

        # 1. منطق المدير/المشرف: يرى جميع الاختبارات ويمكنه تصفيتها
        if user.is_superuser or user.is_admin():
            # لا حاجة لفلترة أساسية هنا، فقط تطبيق معلمات الاستعلام
            pass # ستبقى queryset = Exam.objects.all() قبل الفلاتر

        # 2. منطق المعلم: يرى الاختبارات للمواد التي يدرسها
        elif user.is_teacher():
            try:
                teacher_instance = Teacher.objects.get(user=user)
                if hasattr(teacher_instance, 'teaching_subjects'): # تحقق إذا كان الحقل موجودًا
                    taught_subjects_ids = teacher_instance.teaching_subjects.values_list('id', flat=True)
                    queryset = queryset.filter(subject__id__in=taught_subjects_ids)
                else:
                    pass # سيكمل ليطبق فلاتر query_params على كل الاختبارات المرتبطة بمادة
            except Teacher.DoesNotExist:
                return Exam.objects.none() # لا يوجد بروفايل معلم، فلا يرى شيئًا

        # 3. منطق الطالب: يرى فقط الاختبارات المرتبطة بصفه، شعبته، ومواده
        elif user.is_student():
            student_filter_conditions = Q()
            student_instance = None
            try:
                student_instance = Student.objects.get(user=user)
            except Student.DoesNotExist:
                return Exam.objects.none() # لا يوجد بروفايل طالب، فلا يرى شيئًا
            
            if student_instance.current_class:
                student_filter_conditions |= Q(target_class=student_instance.current_class, target_section__isnull=True, stream_type__isnull=True)
                student_filter_conditions |= Q(target_class=student_instance.current_class, target_section__isnull=True, stream_type=student_instance.current_class.stream_type)
            
            if student_instance.current_section:
                student_filter_conditions |= Q(target_section=student_instance.current_section)
                student_filter_conditions |= Q(
                    target_class=student_instance.current_section.class_obj, 
                    target_section__isnull=True,
                    stream_type__in=[None, student_instance.current_section.stream_type]
                )

            if student_instance.enrolled_subjects.exists():
                subject_ids = student_instance.enrolled_subjects.values_list('id', flat=True)
                # استخدم Q للحفاظ على التجميع
                student_filter_conditions &= Q(subject__id__in=subject_ids)
            else:
                
                return Exam.objects.none()

            queryset = queryset.filter(student_filter_conditions).distinct() # تطبيق شروط الطالب
        else:
            # أي مستخدم آخر غير مسجل الدخول، أو غير معلم/مدير/طالب
            return Exam.objects.none()

        # تطبيق فلاتر معلمات الاستعلام (Query Parameters) بعد الفلاتر الأساسية لكل دور
        subject_id = self.request.query_params.get('subject_id')
        academic_year_id = self.request.query_params.get('academic_year_id')
        academic_term_id = self.request.query_params.get('academic_term_id')
        exam_type = self.request.query_params.get('exam_type')
        exam_date = self.request.query_params.get('exam_date')
        target_class_id = self.request.query_params.get('target_class_id')
        target_section_id = self.request.query_params.get('target_section_id')
        stream_type = self.request.query_params.get('stream_type')

        # استخدام Q objects هنا لتحسين الأداء وتجنب التطبيق المتكرر للفلتر
        query_params_filters = Q()

        if subject_id:
            query_params_filters &= Q(subject_id=subject_id)
        if academic_year_id:
            query_params_filters &= Q(academic_year_id=academic_year_id)
        if academic_term_id:
            query_params_filters &= Q(academic_term_id=academic_term_id)
        if exam_type:
            query_params_filters &= Q(exam_type=exam_type)
        if exam_date:
            query_params_filters &= Q(exam_date=exam_date)
        if target_class_id:
            query_params_filters &= Q(target_class_id=target_class_id)
        if target_section_id:
            query_params_filters &= Q(target_section_id=target_section_id)
        if stream_type:
            query_params_filters &= Q(stream_type=stream_type)
        
        # تطبيق جميع فلاتر query_params مرة واحدة
        queryset = queryset.filter(query_params_filters).distinct()
        
        return queryset

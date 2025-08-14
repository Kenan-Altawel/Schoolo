# exams/views.py
from rest_framework import viewsets, status , generics
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
from classes.models import Section 
from accounts.permissions import CustomPermission
from rest_framework.decorators import action


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [CustomPermission]
    queryset = Exam.objects.all() 

    def get_queryset(self):
        user = self.request.user
        
        # الفلترة الأساسية بناءً على دور المستخدم
        if user.is_admin():
            queryset = Exam.objects.all()
        elif user.is_teacher():
            try:
                teacher = user.teacher_profile 
                queryset = Exam.objects.filter(teacher=teacher)
            except Teacher.DoesNotExist:
                queryset = Exam.objects.none()
        elif user.is_student():
            try:
                student = user.student_profile
                student_section = student.section
                
                queryset = Exam.objects.filter(
                    Q(target_section=student_section) |
                    Q(target_class=student_section.class_obj, target_section__isnull=True)
                )
            except Student.DoesNotExist:
                queryset = Exam.objects.none()
        else:
            queryset = Exam.objects.none()

        # --- تطبيق فلاتر معلمات الاستعلام (Query Parameters) ---
        subject_id = self.request.query_params.get('subject_id')
        academic_year_id = self.request.query_params.get('academic_year_id')
        academic_term_id = self.request.query_params.get('academic_term_id')
        exam_type = self.request.query_params.get('exam_type')
        exam_date = self.request.query_params.get('exam_date')
        target_class_id = self.request.query_params.get('target_class_id')
        target_section_id = self.request.query_params.get('target_section_id')
        stream_type = self.request.query_params.get('stream_type')
        is_conducted = self.request.query_params.get('is_conducted')


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
            query_params_filters &= Q(target_section__stream_type=stream_type)
        if is_conducted is not None: 
            is_conducted_bool = is_conducted.lower() in ['true', '1', 't', 'y']
            query_params_filters &= Q(is_conducted=is_conducted_bool)

        queryset = queryset.filter(query_params_filters).distinct()
        
        return queryset
    def perform_create(self, serializer):
       
        serializer.save()

    def perform_update(self, serializer):
       
        serializer.save()

class ExamConductView(generics.RetrieveUpdateAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsTeacher]

    def patch(self, request, *args, **kwargs):
        exam = self.get_object()
        
        # التحقق من أن المستخدم هو المعلم المسؤول عن هذا الاختبار
        if exam.teacher != request.user.teacher_profile:
            return Response(
                {"detail": _("ليس لديك الصلاحية لإجراء هذا الاختبار.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if exam.is_conducted:
            return Response(
                {"detail": _("هذا الاختبار قد تم إجراؤه بالفعل.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exam.is_conducted = True
        exam.save()
        
        serializer = self.get_serializer(exam)
        
        return Response(
            {"detail": _("تم إجراء الاختبار بنجاح.")},
            status=status.HTTP_200_OK
        )
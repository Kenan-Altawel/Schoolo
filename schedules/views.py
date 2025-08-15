from django.db import models
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count
from academic.models import AcademicYear, AcademicTerm, DayOfWeek, TimeSlot
from classes.models import Class, Section
from students.models import Student
from subject.models import Subject, SectionSubjectRequirement, TeacherSubject
from teachers.models import Teacher
from schedules.models import ClassSchedule
from accounts.models import User
from rest_framework import permissions
from django.core.exceptions import ValidationError
from accounts.permissions import *
from django.db.models import Q


# استيراد الـ Serializers
from .serializers import (
    SubjectWithLessonCountSerializer,
    ClassScheduleSerializer,
)


class SectionSubjectsListView(generics.ListAPIView):
    """
    يعرض قائمة بالمواد الموجودة في شعبة معينة مع عدد الحصص المضافة والمطلوبة.
    Path: /api/classes/{class_id}/sections/{section_id}/subjects/
    """
    serializer_class = SubjectWithLessonCountSerializer
    def get_queryset(self):
        class_id = self.kwargs['class_id']
        section_id = self.kwargs['section_id']

        # التأكد أن الصف والشعبة موجودان
        get_object_or_404(Class, id=class_id)
        section = get_object_or_404(Section, id=section_id)

        queryset = Subject.objects.filter(
            models.Q(class_obj=section.class_obj) |
            models.Q(section=section)
        ).distinct() 

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['class_id'] = self.kwargs['class_id']
        context['section_id'] = self.kwargs['section_id']
        return context




class ClassScheduleCreateView(generics.CreateAPIView):
    """
    لإضافة حصة جديدة إلى الجدول.
    Path: /api/schedules/add/
    """
    serializer_class = ClassScheduleSerializer
    permission_classes = [CustomPermission]

    def create(self, request, *args, **kwargs):

        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            return Response({"detail": "لا يوجد سنة دراسية نشطة حالياً."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            current_academic_term = AcademicTerm.objects.get(
                is_current=True, 
                academic_year=current_academic_year
            )
        except AcademicTerm.DoesNotExist:
            return Response({"detail": "لا يوجد فصل دراسي نشط حالياً."}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data['academic_year'] = current_academic_year.id
        data['academic_term'] = current_academic_term.id

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        response_data = serializer.data

        teacher_id = serializer.validated_data.get('teacher').user_id
        teacher = get_object_or_404(Teacher, user_id=teacher_id)
        preferred_days_objects = teacher.availability.all().order_by('day_of_week')
        teacher_preferred_days = [item.get_day_of_week_display() for item in preferred_days_objects]
        response_data['teacher_preferred_days'] = teacher_preferred_days

        headers = self.get_success_headers(serializer.data)
        
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


       

class ClassScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    لعرض، تعديل، أو حذف حصة معينة في الجدول.
    Path: /api/schedules/{id}/
    """
    queryset = ClassSchedule.objects.all()
    permission_classes = [CustomPermission]
    serializer_class = ClassScheduleSerializer
    lookup_field = 'id' 
    
    def update(self, request, *args, **kwargs):

        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
        except AcademicYear.DoesNotExist:
            return Response({"detail": "لا يوجد سنة دراسية نشطة حالياً."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            current_academic_term = AcademicTerm.objects.get(
                is_current=True, 
                academic_year=current_academic_year
            )
        except AcademicTerm.DoesNotExist:
            return Response({"detail": "لا يوجد فصل دراسي نشط حالياً."}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data['academic_year'] = current_academic_year.id
        data['academic_term'] = current_academic_term.id

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        response_data = serializer.data

        teacher_id = serializer.validated_data.get('teacher').user_id
        teacher = get_object_or_404(Teacher, user_id=teacher_id)
        preferred_days_objects = teacher.availability.all().order_by('day_of_week')
        teacher_preferred_days = [item.get_day_of_week_display() for item in preferred_days_objects]
        response_data['teacher_preferred_days'] = teacher_preferred_days

        headers = self.get_success_headers(serializer.data)
        
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class ClassScheduleListView(generics.ListAPIView):
    """
    لعرض قائمة بجميع الحصص مع إمكانية التصفية بناءً على المستخدم ودوره.
    يمكن للمدراء عرض كل الحصص، بينما يرى المعلمون حصصهم فقط، والطلاب يرون حصص شعبهم.
    """
    serializer_class = ClassScheduleSerializer
    permission_classes = [permissions.IsAuthenticated] # التأكد من أن المستخدم موثق

    def get_queryset(self):
        # قاعدة البيانات الأساسية لجميع الحصص
        queryset = ClassSchedule.objects.all()
        user = self.request.user

        # إذا لم يكن المستخدم موثقاً، لا تُرجع شيئاً.
        # على الرغم من وجود permission_classes، هذه خطوة أمان إضافية.
        if not user.is_authenticated:
            queryset= ClassSchedule.objects.none()

        # منطق المسؤول والمشرف:
        # إذا كان المستخدم مشرفاً عاماً، يمكنه رؤية جميع الحصص.
        if user.is_superuser or user.is_admin(): # افترضنا وجود دالة is_admin()
            queryset = queryset

        # منطق المعلم:
        # إذا كان المستخدم معلماً، يُرجع له الحصص التي يدرسها فقط.
        is_teacher_role = user.is_teacher() # افترضنا وجود دالة is_teacher()
        if is_teacher_role:
            # يجب أن يكون لدى المستخدم كائن teacher مرتبط به
            try:
                teacher_obj = Teacher.objects.filter(user=user).first()
                queryset = queryset.filter(teacher=teacher_obj)
            except Teacher.DoesNotExist:
                queryset = ClassSchedule.objects.none()

        # منطق الطالب:
        # إذا كان المستخدم طالباً، يُرجع له الحصص الخاصة بشعبته الحالية.
        is_student_role = user.is_student() # افترضنا وجود دالة is_student()
        if is_student_role:
            # يجب أن يكون لدى المستخدم كائن student مرتبط به
            try:
                student_obj = Student.objects.filter(user=user).first()
                if student_obj.section:
                    queryset= queryset.filter(section=student_obj.section)
            except Student.DoesNotExist:
                queryset= ClassSchedule.objects.none()

        teacher_id = self.request.query_params.get('teacher_id')
        subject_id = self.request.query_params.get('subject_id')
        day_of_week = self.request.query_params.get('day_of_week')
        section_id = self.request.query_params.get('section_id')
        
        # تطبيق الفلترة على الـ queryset
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        if day_of_week:
            try:
                day_of_week_int = int(day_of_week)
                queryset = queryset.filter(day_of_week=day_of_week_int)
            except (ValueError, TypeError):
                pass
        
        if section_id:
            queryset = queryset.filter(section_id=section_id)
            
        return queryset.distinct()
        

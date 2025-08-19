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
from django.db import transaction
from rest_framework.exceptions import ValidationError as DRFValidationError


# استيراد الـ Serializers
from .serializers import (
    SubjectWithLessonCountSerializer,
    ClassScheduleSerializer,
    SubjectRemainingLessonsSerializer,
)


def _calculate_remaining_lessons(section: Section, subject: Subject, academic_year: AcademicYear, academic_term: AcademicTerm) -> int:
    """احسب عدد الحصص المتبقية المطلوبة لهذه المادة في هذه الشعبة ضمن العام والفصل الحاليين."""
    try:
        requirement = SectionSubjectRequirement.objects.get(section=section, subject=subject)
        required = requirement.weekly_lessons_required
    except SectionSubjectRequirement.DoesNotExist:
        required = subject.default_weekly_lessons

    added = ClassSchedule.objects.filter(
        section=section,
        subject=subject,
        academic_year=academic_year,
        academic_term=academic_term,
    ).count()
    remaining = required - added
    return remaining if remaining > 0 else 0


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
    # def get_queryset(self):
    #     user = self.request.user
    #     class_id = self.kwargs['class_id']
    #     section_id = self.kwargs['section_id']

    #     # 1. التحقق من وجود الصف والشعبة
    #     # هذا يضمن أن IDs الموجودة في الـ URL صحيحة
    #     school_class = get_object_or_404(Class, id=class_id)
    #     section = get_object_or_404(Section, id=section_id, class_obj=school_class)

    #     # 2. منطق الوصول للمدير/المشرف العام
    #     if user.is_superuser or user.is_admin:
    #         queryset = Subject.objects.filter(
    #             Q(class_obj=school_class) | Q(section=section)
    #         ).distinct()
    #         return queryset
        
    #     elif user.is_student:
    #         try:
    #             student = user.student 
    #             student_section = student.section

    #             if student.section.id != section.id:
    #                 return Subject.objects.none()
                
    #             queryset = Subject.objects.filter(section=student.section)
    #             return queryset
            
    #         except Student.DoesNotExist:
    #             return Subject.objects.none()
        
    #     return Subject.objects.none()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['class_id'] = self.kwargs['class_id']
        context['section_id'] = self.kwargs['section_id']
        return context


class SectionSubjectsRemainingListView(generics.ListAPIView):
    """
    يعرض قائمة مبسطة بكل المواد في شعبة محددة مع عدد الحصص المتبقية لكل مادة.
    Path: /api/sections/<section_id>/subjects/
    """
    serializer_class = SubjectRemainingLessonsSerializer

    def get_queryset(self):
        section_id = self.kwargs['section_id']
        section = get_object_or_404(Section, id=section_id)
        queryset = Subject.objects.filter(
            models.Q(class_obj=section.class_obj) |
            models.Q(section=section)
        ).distinct()
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
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

        # تفضيلات أيام المعلم
        teacher_id = serializer.validated_data.get('teacher').user_id
        teacher = get_object_or_404(Teacher, user_id=teacher_id)
        preferred_days_objects = teacher.availability.all().order_by('day_of_week')
        teacher_preferred_days = [item.day_of_week.name_ar for item in preferred_days_objects]
        response_data['teacher_preferred_days'] = teacher_preferred_days

        # عدد الحصص المتبقية لهذه المادة في هذه الشعبة
        obj = serializer.instance
        remaining_lessons = _calculate_remaining_lessons(
            section=obj.section,
            subject=obj.subject,
            academic_year=obj.academic_year,
            academic_term=obj.academic_term,
        )
        response_data['remaining_lessons'] = remaining_lessons

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
        teacher_preferred_days = [item.day_of_week.name_ar for item in preferred_days_objects]
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
        

class ClassScheduleBulkCreateView(APIView):
    """
    إضافة قائمة من الحصص لشعبة واحدة دفعة واحدة.
    Path: /api/sections/<section_id>/schedules/bulk_add/

    Body مثال:
    {
        "schedules": [
            {"subject": 1, "teacher": 3, "day_of_week": 2, "time_slot": 7},
            {"subject": 2, "teacher": 4, "day_of_week": 3, "time_slot": 5}
        ]
    }
    """
    permission_classes = [CustomPermission]

    def post(self, request, *args, **kwargs):
        # الحصول على العام والفصل الحاليين
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

        payload = request.data
        # أخذ القسم من الـ URL فقط
        section_id = kwargs.get('section_id')
        schedules = payload.get('schedules') or []

        if not isinstance(schedules, list) or len(schedules) == 0:
            return Response({"detail": "الرجاء إرسال قائمة 'schedules' غير فارغة."}, status=status.HTTP_400_BAD_REQUEST)

        # التأكد من وجود الشعبة
        section = get_object_or_404(Section, id=section_id)

        # التحقق من التكرارات داخل نفس الطلب
        section_slot_keys = set()
        teacher_slot_keys = set()
        for idx, item in enumerate(schedules):
            try:
                subject_id = int(item.get('subject'))
                teacher_id = int(item.get('teacher'))
                day_id = int(item.get('day_of_week'))
                slot_id = int(item.get('time_slot'))
            except (TypeError, ValueError):
                return Response({"detail": f"السجل رقم {idx} يحتوي على قيم غير صحيحة."}, status=status.HTTP_400_BAD_REQUEST)

            # منع تضارب داخل نفس الدُفعة لنفس الشعبة
            key_section = (section.id, day_id, slot_id)
            if key_section in section_slot_keys:
                return Response({"detail": f"تكرار لنفس الشعبة في نفس اليوم والفترة داخل نفس الطلب عند السجل رقم {idx}."}, status=status.HTTP_400_BAD_REQUEST)
            section_slot_keys.add(key_section)

            # منع تضارب داخل نفس الدُفعة لنفس المعلم
            key_teacher = (teacher_id, day_id, slot_id)
            if key_teacher in teacher_slot_keys:
                return Response({"detail": f"المعلم مكرر في نفس اليوم والفترة داخل نفس الطلب عند السجل رقم {idx}."}, status=status.HTTP_400_BAD_REQUEST)
            teacher_slot_keys.add(key_teacher)

        created_objects = []
        response_items = []
        errors = []

        # عملية واحدة ذرّية
        with transaction.atomic():
            for idx, item in enumerate(schedules):
                item_data = {
                    'subject': item.get('subject'),
                    'section': section.id,
                    'teacher': item.get('teacher'),
                    'academic_year': current_academic_year.id,
                    'academic_term': current_academic_term.id,
                    'day_of_week': item.get('day_of_week'),
                    'time_slot': item.get('time_slot'),
                }

                serializer = ClassScheduleSerializer(data=item_data)
                if not serializer.is_valid():
                    errors.append({"index": idx, "errors": serializer.errors})
                    continue

                obj = serializer.save()
                created_objects.append(obj)

                # إعداد بيانات الإرجاع مع تفضيلات المعلم للأيام
                # نحصل على أيام التفضيلات مرتبة لعرضها
                try:
                    teacher_obj = Teacher.objects.get(pk=item_data['teacher'])
                    preferred_days_objects = teacher_obj.availability.all().order_by('day_of_week')
                    teacher_preferred_days = [d.day_of_week.name_ar for d in preferred_days_objects]
                except Teacher.DoesNotExist:
                    teacher_preferred_days = []

                item_response = ClassScheduleSerializer(obj).data
                item_response['teacher_preferred_days'] = teacher_preferred_days
                # المتبقي بعد إضافة هذا السجل
                item_response['remaining_lessons'] = _calculate_remaining_lessons(
                    section=section,
                    subject=obj.subject,
                    academic_year=obj.academic_year,
                    academic_term=obj.academic_term,
                )
                response_items.append(item_response)

            if errors:
                # أي خطأ -> نرمي DRF ValidationError لضمان التراجع عن كل الإنشاءات
                raise DRFValidationError({"detail": "فشل إنشاء بعض السجلات.", "errors": errors})

        return Response(response_items, status=status.HTTP_201_CREATED)
        

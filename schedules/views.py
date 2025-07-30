from django.db import models
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count

# استيراد الموديلات من التطبيقات الصحيحة
from academic.models import AcademicYear, AcademicTerm, DayOfWeek, TimeSlot
from classes.models import Class, Section
from subject.models import Subject, SectionSubjectRequirement, TeacherSubject
from teachers.models import Teacher, TeacherAvailability
from schedules.models import ClassSchedule, \
    ProposedClassSchedule  # تأكد من استيراد هذه الموديلات من تطبيق schedules الخاص بك
from accounts.models import User

# استيراد الـ Serializers
from .serializers import (
    SubjectWithLessonCountSerializer,
    TeacherSerializer,
    ClassScheduleSerializer,
    DayOfWeekSerializer,  # إذا أردت عرض أيام الأسبوع بشكل منفصل
    TimeSlotSerializer,  # إذا أردت عرض الفترات الزمنية بشكل منفصل
)


# ملاحظة: لم يتم تضمين Authentication و Permissions هنا، يجب إضافتها.
# مثال: from rest_framework.permissions import IsAuthenticated, IsAdminUser

class SectionSubjectsListView(generics.ListAPIView):
    """
    يعرض قائمة بالمواد الموجودة في شعبة معينة مع عدد الحصص المضافة والمطلوبة.
    Path: /api/classes/{class_id}/sections/{section_id}/subjects/
    """
    serializer_class = SubjectWithLessonCountSerializer

    # permission_classes = [IsAuthenticated, IsAdminUser] # مثال على إضافة الصلاحيات

    def get_queryset(self):
        class_id = self.kwargs['class_id']
        section_id = self.kwargs['section_id']

        # التأكد أن الصف والشعبة موجودان
        get_object_or_404(Class, id=class_id)
        section = get_object_or_404(Section, id=section_id)

        # فلترة المواد التي تنتمي لهذا الصف أو الشعبة أو العام الدراسي
        # هذا يعتمد على منطق ربط المواد بالصفوف/الشعب في موديل Subject
        # هنا نفترض أن المادة يمكن أن ترتبط بـ Class أو Section
        queryset = Subject.objects.filter(
            models.Q(class_obj=section.class_obj) |
            models.Q(section=section)
        ).distinct()  # للتأكد من عدم تكرار المواد

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['class_id'] = self.kwargs['class_id']
        context['section_id'] = self.kwargs['section_id']
        return context


class SubjectTeachersListView(generics.ListAPIView):
    """
    يعرض قائمة بالمعلمين الذين يدرّسون مادة معينة.
    Path: /api/subjects/{subject_id}/teachers/
    """
    serializer_class = TeacherSerializer

    # permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        subject_id = self.kwargs['subject_id']
        subject = get_object_or_404(Subject, id=subject_id)

        # جلب المعلمين الذين يدرسون هذه المادة عبر TeacherSubject
        teachers_ids = TeacherSubject.objects.filter(subject=subject).values_list('teacher_id', flat=True)
        return Teacher.objects.filter(id__in=teachers_ids)


class ClassScheduleCreateView(generics.CreateAPIView):
    """
    لإضافة حصة جديدة إلى الجدول.
    Path: /api/schedules/add/
    """
    serializer_class = ClassScheduleSerializer

    # permission_classes = [IsAuthenticated, IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # منطق اقتراح الأيام المفضلة للمعلم (للعرض فقط، القرار للمدير)
        teacher_id = serializer.validated_data.get('teacher').id
        teacher = get_object_or_404(Teacher, id=teacher_id)

        # جلب الأيام المفضلة من TeacherAvailability
        preferred_days_objects = teacher.availability.all().order_by('day_of_week')
        teacher_preferred_days = [item.get_day_of_week_display() for item in preferred_days_objects]

        try:
            self.perform_create(serializer)
        except Exception as e:  # يمكن أن تكون ValidationError من clean method في الموديل
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response_data = serializer.data
        response_data['teacher_preferred_days'] = teacher_preferred_days  # لإظهار الأيام المفضلة للمدير

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class ClassScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    لعرض، تعديل، أو حذف حصة معينة في الجدول.
    Path: /api/schedules/{id}/
    """
    queryset = ClassSchedule.objects.all()
    serializer_class = ClassScheduleSerializer
    lookup_field = 'id'  # للتأكد من استخدام 'id' في الـ URL

    # permission_classes = [IsAuthenticated, IsAdminUser]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_update(serializer)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance,
            # otherwise the original saved object will be returned.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SectionClassSchedulesView(generics.ListAPIView):
    """
    يعرض جميع الحصص المجدولة لصف وشعبة معينين.
    Path: /api/classes/{class_id}/sections/{section_id}/schedules/
    """
    serializer_class = ClassScheduleSerializer

    # permission_classes = [IsAuthenticated] # يمكن أن يكون متاحاً للمعلمين والطلاب أيضاً

    def get_queryset(self):
        class_id = self.kwargs['class_id']
        section_id = self.kwargs['section_id']

        # التأكد أن الصف والشعبة موجودان
        get_object_or_404(Class, id=class_id)
        get_object_or_404(Section, id=section_id)

        # جلب الجداول الخاصة بهذه الشعبة
        return ClassSchedule.objects.filter(
            section_id=section_id
        ).order_by('academic_year__name', 'academic_term__name', 'day_of_week', 'period')

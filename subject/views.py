# subject/views.py
from rest_framework import viewsets, status , generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _

from academic.models import AcademicTerm, AcademicYear
from schedules.models import ClassSchedule
from .models import Subject, SectionSubjectRequirement
from .serializers import *
from classes.models import Class, Section
from classes.serializers import TaughtSectionSerializer
from django.db import transaction
from django.db.models import Q
from accounts.permissions import *
from django_filters.rest_framework import DjangoFilterBackend
from .filters import *
from students.models import Student
from teachers.models import Teacher 
from .models import TeacherSubject
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound


class CustomPermission(permissions.BasePermission):
   
    def has_permission(self, request, view):
        if not request.user :
            return False

        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return IsAdminOrSuperuser().has_permission(request, view)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [CustomPermission]
    filter_backends = [DjangoFilterBackend] 
    filterset_class = SubjectFilter 

    def get_queryset(self):
        user = self.request.user
        
        # إذا كان المستخدم غير موثق، لا يعرض له أي شيء
        if not user.is_authenticated:
            return Subject.objects.none()

        # 1. للمدراء والمشرفين (Admin/Superuser)
        # يمكن للمدراء رؤية كل المواد
        if user.is_superuser or user.is_admin():
            return self.queryset

        # 2. للمعلمين
        # يمكن للمعلم رؤية المواد التي يدرسها فقط
        if user.is_teacher():
            try:
                # الوصول إلى كائن المعلم باستخدام related_name 'teacher_profile'
                teacher_instance = user.teacher_profile
                # الحصول على IDs جميع المواد المرتبطة بالمعلم من خلال TeacherSubject
                taught_subject_ids = teacher_instance.teaching_subjects.values_list('subject_id', flat=True)
                return self.queryset.filter(id__in=taught_subject_ids)
            except Teacher.DoesNotExist:
                return Subject.objects.none()

        # 3. للطلاب
        # يمكن للطالب رؤية المواد الخاصة بشعبته وصفه فقط
        if user.is_student():
            try:
                # الوصول إلى كائن الطالب باستخدام related_name 'student'
                student_instance = user.student

                # إذا لم يكن للطالب شعبة مرتبطة، لا يوجد أي مواد ليعرضها
                if not student_instance.section:
                    return Subject.objects.none()

                # الوصول إلى الشعبة والصف الخاص بالطالب
                student_section = student_instance.section
                student_class = student_section.class_obj

                # فلترة المواد العامة التي تُدرّس في الصف بأكمله
                general_subjects = self.queryset.filter(
                    class_obj=student_class,
                    section__isnull=True,
                    stream_type__in=['General', None]
                )

                # فلترة المواد الخاصة بمسار الطالب إذا كان للشعبة مسار محدد
                specialized_subjects = self.queryset.none()
                if student_section.stream_type:
                    specialized_subjects = self.queryset.filter(
                        section=student_section,
                        class_obj=student_class,
                        stream_type=student_section.stream_type
                    )
                
                # دمج قائمة المواد العامة والمتخصصة وإزالة أي تكرار
                return (general_subjects | specialized_subjects).distinct()
            except Student.DoesNotExist:
                return Subject.objects.none()
        
        # 4. للمستخدمين الآخرين
        return Subject.objects.none()

    def perform_create(self, serializer):
        with transaction.atomic():
            subject_instance = serializer.save()
            self._create_section_subject_requirements(subject_instance)

    def perform_update(self, serializer):
        with transaction.atomic():
            subject_instance = serializer.save()
            SectionSubjectRequirement.objects.filter(subject=subject_instance).delete()
            self._create_section_subject_requirements(subject_instance)

    def _create_section_subject_requirements(self, subject_instance):
        weekly_lessons = subject_instance.default_weekly_lessons

        # 1. الأولوية للربط بشعبة محددة:
        # هذا الجزء سينفذ إذا لم يتم اعتراضه بواسطة validation السيريالايزر الجديد
        # (أي أن المادة لم تكن "عامة" وتم ربطها بشعبة محددة، وهذا لن يحدث الآن).
        if subject_instance.section:
            section = subject_instance.section
            if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
                SectionSubjectRequirement.objects.create(
                    section=section,
                    subject=subject_instance,
                    weekly_lessons_required=weekly_lessons,
                )
                print(
                    f"Created SSR for specific section: {section.name} (ID: {section.id}) for subject '{subject_instance.name}'.")
            else:
                print(
                    f"SSR already exists for specific section {section.name} and subject '{subject_instance.name}'. Skipping creation.")
            return  # إذا كانت المادة مرتبطة بشعبة محددة، ننتهي من الدالة هنا.

        # 2. الربط لصف كامل (ينفذ هذا الجزء فقط إذا لم يتم تحديد شعبة محددة للمادة).
        if subject_instance.class_obj:
            sections_to_link = Section.objects.filter(class_obj=subject_instance.class_obj)

            # **تعديل:** تعريف "المادة العامة للصف" يشمل stream_type=None أو 'General'
            is_subject_general_for_class = (subject_instance.stream_type is None) or (
                        subject_instance.stream_type == 'General')

            if not is_subject_general_for_class:  # إذا كانت المادة ليست عامة للصف (أي Scientific أو Literary)
                # اربط فقط بالشعب ذات stream_type المطابق أو الشعب العامة (stream_type is None).
                sections_to_link = sections_to_link.filter(
                    Q(stream_type=subject_instance.stream_type) | Q(stream_type__isnull=True)
                )
                print(
                    f"Linking subject '{subject_instance.name}' (Stream: {subject_instance.stream_type}) to sections in class '{subject_instance.class_obj.name}' with matching or null stream_type.")

            else:  
                print(
                    f"Linking subject '{subject_instance.name}' (General for Class) to ALL sections in class '{subject_instance.class_obj.name}'.")

            if not sections_to_link.exists():
                print(
                    f"Warning: No sections found for class '{subject_instance.class_obj.name}' matching criteria. No SSRs created for subject '{subject_instance.name}'.")
                return

            for section in sections_to_link:
                if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
                    SectionSubjectRequirement.objects.create(
                        section=section,
                        subject=subject_instance,
                        weekly_lessons_required=weekly_lessons,
                    )
                    print(
                        f"Created SSR for section {section.name} (ID: {section.id}) for subject '{subject_instance.name}'.")
                else:
                    print(
                        f"SSR already exists for section {section.name} and subject '{subject_instance.name}'. Skipping creation.")
        else:
            print(
                f"Error: Subject '{subject_instance.name}' is not linked to a class or specific section. No SectionSubjectRequirement created.")


class SubjectTeachersListView(generics.ListAPIView):
    serializer_class = TeacherSubjectSerializer
    permission_classes = [CustomPermission]

    def get_queryset(self):
        subject_id = self.kwargs['subject_id']
        return TeacherSubject.objects.filter(subject_id=subject_id)
    

class SubjectIconListView(generics.ListAPIView):
    """
    عرض قائمة بجميع أيقونات المواد الدراسية.
    """
    queryset = SubjectIcon.objects.all()
    serializer_class = SubjectIconSerializer
    permission_classes = [IsAdminOrSuperuser]
    


class TeacherTaughtSectionsView(ListAPIView):
    """
    عرض قائمة بجميع الشعب التي يدرسها الأستاذ الحالي، مع مراعاة العام والفصل الدراسي الحالي.
    """
    serializer_class = TaughtSectionSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        user = self.request.user
        teacher = Teacher.objects.get(user=user)

        try:
            current_academic_year = AcademicYear.objects.get(is_current=True)
            current_academic_term = AcademicTerm.objects.get(
                is_current=True, 
                academic_year=current_academic_year
            )
        except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
            raise NotFound("لا يوجد عام أو فصل دراسي حالي محدد.")
        
        sections_taught_ids = ClassSchedule.objects.filter(
            teacher=teacher,
            academic_year=current_academic_year,
            academic_term=current_academic_term
        ).values_list('section_id', flat=True).distinct()
        
        # 2. البحث عن كائنات الشعب (Section objects) باستخدام هذه المعرفات
        queryset = Section.objects.filter(id__in=sections_taught_ids)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        response_data = {
            "sections you are teaching": queryset.count(),
            "sections": serializer.data
        }
        
        return Response(response_data)
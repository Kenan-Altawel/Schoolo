# exams/views.py
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, status , generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q , Avg
from rest_framework import permissions # يجب استيراد permissions
from django.utils.translation import gettext_lazy as _
from accounts.permissions import *
from .serializers import *
from .models import *
from accounts.models import User 
from teachers.models import Teacher
from students.models import Student 
from classes.models import Section 
from accounts.permissions import CustomPermission
from rest_framework.decorators import action
from django.utils import timezone

class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [CustomPermission]
    queryset = Exam.objects.all() 

    def get_queryset(self):
        user = self.request.user
        
        # الفلترة الأساسية بناءً على دور المستخدم
        if user.is_superuser or user.is_admin():
            queryset = Exam.objects.all()
        elif user.is_teacher():
            try:
                teacher = user.teacher_profile 
                queryset = Exam.objects.filter(teacher=teacher)
            except Teacher.DoesNotExist:
                queryset = Exam.objects.none()
        elif user.is_student():
            try:
                student = user.student
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
        user = self.request.user
        exam_type = self.request.data.get('exam_type')

        if user.is_teacher():
            allowed_exam_types = ['quiz', 'assignment']
            if exam_type not in allowed_exam_types:
                raise ValidationError({
                    "detail": _("المعلمون مسموح لهم فقط بإنشاء اختبارات من نوع quiz أو assignment.")
                })

        serializer.save(teacher=self.request.user.teacher_profile)

    def perform_update(self, serializer):
        """
        يسمح للمعلم بتعديل الاختبارات التي قام بإنشائها فقط.
        """
        user = self.request.user
        exam = self.get_object()

        # التحقق من أن المستخدم الحالي هو معلم الاختبار
        if user.is_teacher() and exam.teacher != user.teacher_profile:
            raise PermissionDenied(
                _("ليس لديك الصلاحية لتعديل هذا الاختبار.")
            )

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



class GradeViewSet(viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    queryset = Grade.objects.all()
    permission_classes = [IsAuthenticatedAndTeacherForWrites]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.is_admin():
            queryset= Grade.objects.all()
        elif user.is_teacher():
            try:
                teacher = user.teacher_profile
                queryset= Grade.objects.filter(exam__teacher=teacher)
            except Teacher.DoesNotExist:
                queryset= Grade.objects.none()
        elif user.is_student():
            try:
                student = user.student
                queryset= Grade.objects.filter(student=student)
            except Student.DoesNotExist:
                queryset= Grade.objects.none()
        else :
            queryset= Grade.objects.none()
            
        subject_id = self.request.query_params.get('subject_id')
        exam_type = self.request.query_params.get('exam_type')
        target_class_id = self.request.query_params.get('target_class_id')
        target_section_id = self.request.query_params.get('section_id')
        stream_type = self.request.query_params.get('stream_type')


        query_params_filters = Q()

        if subject_id:
            query_params_filters &= Q(exam__subject_id=subject_id)
        if exam_type:
            query_params_filters &= Q(exam__exam_type=exam_type)
        if target_class_id:
            query_params_filters &= Q(exam__target_class_id=target_class_id)
        if target_section_id:
            query_params_filters &= (
                Q(exam__target_section_id=target_section_id) |
                Q(exam__target_section__isnull=True, student__section_id=target_section_id)
            )

        if stream_type:
            query_params_filters &= Q(student__section__stream_type=stream_type)


        queryset = queryset.filter(query_params_filters).distinct()
        
        return queryset
    def perform_create(self, serializer):
        teacher = self.request.user.teacher_profile
        exam = serializer.validated_data['exam']
        student = serializer.validated_data['student']

        if exam.teacher != teacher:
            raise PermissionDenied(_("لا يمكنك إنشاء علامات لاختبار لا تخصك."))

        if not exam.is_conducted:
            raise ValidationError({
                "exam": _("لا يمكن إضافة علامات لاختبار لم يتم إجراؤه بعد.")
            })

        if exam.target_section and student.section != exam.target_section:
            raise ValidationError({
                "student": _("الطالب لا ينتمي إلى الشعبة المستهدفة لهذا الاختبار.")
            })
        elif exam.target_class and student.section.class_obj != exam.target_class:
            raise ValidationError({
                "student": _("الطالب لا ينتمي إلى الصف المستهدف لهذا الاختبار.")
            })
        
        serializer.validated_data['graded_at'] = timezone.now()
        serializer.save()

    def perform_update(self, serializer):
        teacher = self.request.user.teacher_profile
        exam = serializer.validated_data.get('exam', self.get_object().exam)
        student = serializer.validated_data['student']

        if exam.teacher != teacher:
            self.permission_denied(self.request, message=_("لا يمكنك تعديل علامات لاختبار لا تخصك."))
        if exam.target_section and student.section != exam.target_section:
            raise ValidationError({
                "student": _("الطالب لا ينتمي إلى الشعبة المستهدفة لهذا الاختبار.")
            })
        elif exam.target_class and student.section.class_obj != exam.target_class:
            raise ValidationError({
                "student": _("الطالب لا ينتمي إلى الصف المستهدف لهذا الاختبار.")
            })

        serializer.validated_data['graded_at'] = timezone.now()
        serializer.save()
        
    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=False, methods=['get'])
    def calculate_student_averages(self, request):
        student_id = request.query_params.get('student_id')
        academic_year_id = request.query_params.get('academic_year_id')
        academic_term_id = request.query_params.get('academic_term_id')

        if not student_id:
            return Response(
                {"detail": _("يجب توفير رقم تعريف الطالب.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {"detail": _("الطالب غير موجود.")},
                status=status.HTTP_404_NOT_FOUND
            )

        # التحقق من الصلاحيات
        user = self.request.user
        if user.is_teacher() and student.section.teacher != user.teacher_profile:
            return Response(
                {"detail": _("ليس لديك الصلاحية لعرض معدلات هذا الطالب.")},
                status=status.HTTP_403_FORBIDDEN
            )
        if user.is_student() and student.user != user:
            return Response(
                {"detail": _("ليس لديك الصلاحية لعرض معدلات طالب آخر.")},
                status=status.HTTP_403_FORBIDDEN
            )

        # فلترة العلامات بناءً على الطالب والسنة والفصل (إذا تم توفيرهما)
        grades_queryset = Grade.objects.filter(student=student)
        
        if academic_year_id:
            grades_queryset = grades_queryset.filter(exam__academic_year_id=academic_year_id)
        
        if academic_term_id:
            grades_queryset = grades_queryset.filter(exam__academic_term_id=academic_term_id)

        # حساب معدلات كل نوع امتحان
        averages = grades_queryset.values('exam__exam_type').annotate(average_score=Avg('score'))

        # تجهيز البيانات للرد
        averages_by_type = {item['exam__exam_type']: item['average_score'] for item in averages}
        
        midterm_average = averages_by_type.get('midterm', None)
        final_average = averages_by_type.get('final', None)
        quiz_average = averages_by_type.get('quiz', None)
        assignment_average = averages_by_type.get('assignment', None)

        term_average = None
        if midterm_average is not None and final_average is not None:
            term_average = (midterm_average + final_average) / 2
        
        activities_average = None
        activity_scores = [score for score in [quiz_average, assignment_average] if score is not None]
        if activity_scores:
            activities_average = sum(activity_scores) / len(activity_scores)

        response_data = {
            "student_id": student.id,
            "student_name": student.user.get_full_name(),
            "academic_year_id": academic_year_id,
            "academic_term_id": academic_term_id,
            "midterm_average": round(midterm_average, 2) if midterm_average is not None else None,
            "final_average": round(final_average, 2) if final_average is not None else None,
            "quiz_average": round(quiz_average, 2) if quiz_average is not None else None,
            "assignment_average": round(assignment_average, 2) if assignment_average is not None else None,
            "activities_average": round(activities_average, 2) if activities_average is not None else None,
            "term_average": round(term_average, 2) if term_average is not None else None,
        }
        
        # حساب معدل السنة الدراسية إذا لم يتم تحديد الفصل
        if academic_year_id and not academic_term_id:
            # يجب أن يكون لديك منطق للحصول على فصلي السنة الدراسية
            # يمكن افتراض وجود فصلين لكل سنة دراسية
            term_1_grades = Grade.objects.filter(
                student=student, 
                exam__academic_year_id=academic_year_id,
                exam__academic_term_id=1  # مثال: رقم تعريف الفصل الأول
            )
            term_2_grades = Grade.objects.filter(
                student=student, 
                exam__academic_year_id=academic_year_id,
                exam__academic_term_id=2  # مثال: رقم تعريف الفصل الثاني
            )

            term_1_midterm = term_1_grades.filter(exam__exam_type='midterm').aggregate(Avg('score'))['score__avg']
            term_1_final = term_1_grades.filter(exam__exam_type='final').aggregate(Avg('score'))['score__avg']
            term_1_avg = (term_1_midterm + term_1_final) / 2 if term_1_midterm and term_1_final else None

            term_2_midterm = term_2_grades.filter(exam__exam_type='midterm').aggregate(Avg('score'))['score__avg']
            term_2_final = term_2_grades.filter(exam__exam_type='final').aggregate(Avg('score'))['score__avg']
            term_2_avg = (term_2_midterm + term_2_final) / 2 if term_2_midterm and term_2_final else None

            yearly_average = None
            if term_1_avg is not None and term_2_avg is not None:
                yearly_average = (term_1_avg + term_2_avg) / 2
            
            response_data['yearly_average'] = round(yearly_average, 2) if yearly_average is not None else None

        return Response(response_data, status=status.HTTP_200_OK)
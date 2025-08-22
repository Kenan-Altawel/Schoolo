from django.shortcuts import render
from rest_framework.views import APIView
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Count, Max
from accounts.permissions import IsAdminOrSuperuser
from students.models import Student
from classes.models import Class, Section
from .models import *
from .serializers import *
from grading.grade_calculator import GradeCalculator
from academic.models import AcademicYear
from rest_framework import status
from rest_framework.response import Response
from .filters import StudentProgressionIssueFilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

class StudentPromotionView(APIView):
    permission_classes = [IsAdminOrSuperuser]

    def _promote_students(self, students, current_year, previous_year):
        promotion_results = {
            'promoted': 0,
            'failed': 0,
            'graduated': 0,
            'issues': 0,
        }
        grade_calculator = GradeCalculator()
        for student in students:
            overall_average = grade_calculator.calculate_overall_average(
                student_id=student.pk,
                academic_year_id=previous_year.pk
            )
            from_class = student.student_class
            from_section = student.section

            # إعداد البيانات التي سيتم تحديثها أو إنشاؤها
            progression_data = {
                'student': student,
                'academic_year': current_year,
                'overall_average': overall_average,
                'from_class': from_class,
                'from_section': from_section,
            }

            # المنطق لفرز الطلاب
            if overall_average is None or overall_average < 50:
                progression_data.update({
                    'result_status': 'failed',
                    'is_promoted': False,
                    'to_class': from_class,
                    'to_section': from_section,
                    'notes': _("المعدل العام أقل من درجة النجاح المطلوبة.")
                })
                StudentProgression.objects.update_or_create(
                    student=student, academic_year=current_year, defaults=progression_data
                )
                promotion_results['failed'] += 1
            elif from_class and not from_class.next_class:
                student.student_class = None
                student.section = None
                student.save()
                
                progression_data.update({
                    'result_status': 'graduated',
                    'is_promoted': False,
                    'to_class': None,
                    'to_section': None,
                    'notes': _("أتم الطالب دراسته بنجاح وتخرج.")
                })
                StudentProgression.objects.update_or_create(
                    student=student, academic_year=current_year, defaults=progression_data
                )
                promotion_results['graduated'] += 1
            else:
                try:
                    next_class = from_class.next_class
                    to_section = Section.objects.filter(
                        class_obj=next_class,
                        academic_year=current_year,
                        is_active=True,
                        stream_type=from_section.stream_type
                    ).annotate(
                        student_count=Count('students')
                    ).filter(
                        student_count__lt=F('capacity')
                    ).order_by('student_count').first()

                    if not to_section:
                        progression_data.update({
                            'result_status': 'failed',
                            'is_promoted': False,
                            'to_class': from_class,
                            'to_section': from_section
                        })
                        progression, created = StudentProgression.objects.update_or_create(
                            student=student, academic_year=current_year, defaults=progression_data
                        )
                        
                        StudentProgressionIssue.objects.update_or_create(
                            student_progression=progression,
                            issue_type='no_available_section',
                            defaults={'description': _("لا توجد شعبة متاحة في الصف التالي لاستيعاب الطالب.")}
                        )
                        promotion_results['issues'] += 1
                    else:
                        student.student_class = next_class
                        student.section = to_section
                        student.save()
                        
                        progression_data.update({
                            'result_status': 'promoted',
                            'is_promoted': True,
                            'to_class': next_class,
                            'to_section': to_section,
                        })
                        progression, created = StudentProgression.objects.update_or_create(
                            student=student, academic_year=current_year, defaults=progression_data
                        )
                        
                        # Mark the issue as resolved if it exists
                        StudentProgressionIssue.objects.filter(
                            student_progression__student=student,
                            issue_type='no_available_section'
                        ).update(is_resolved=True, description=_("تم حل المشكلة يدويا وترقية الطالب."))
                        
                        promotion_results['promoted'] += 1
                except Class.DoesNotExist:
                    promotion_results['issues'] += 1
        return promotion_results
    def post(self, request, *args, **kwargs):
        """
        Performs automatic promotion for all students in the previous academic year.
        """
        try:
            with transaction.atomic():
                try:
                    current_year = AcademicYear.objects.get(is_current=True)
                    previous_year = AcademicYear.objects.filter(end_date__lt=current_year.start_date).order_by('-end_date').first()
                    if not previous_year:
                        return Response({"detail": _("لا يوجد عام دراسي سابق محدد.")}, status=status.HTTP_400_BAD_REQUEST)
                except AcademicYear.DoesNotExist:
                    return Response({"detail": _("لا يوجد عام دراسي حالي محدد.")}, status=status.HTTP_400_BAD_REQUEST)
                
                if StudentProgression.objects.filter(academic_year=current_year).exists():
                    return Response(
                        {"detail": _("عملية الترقية قد تمت بالفعل لهذا العام الدراسي. يرجى إعادة ضبطها أولاً إذا كنت ترغب في إعادة التشغيل."), "hint": "قم بإرسال طلب POST إلى مسار /api/promotion/reset/"},
                        status=status.HTTP_409_CONFLICT
                    )
                
                students = Student.objects.filter(
                    section__academic_year=previous_year
                ).select_related('student_class', 'section')
                
                if not students.exists():
                    return Response({"detail": _("لا يوجد طلاب مسجلون في العام الدراسي السابق.")}, status=status.HTTP_200_OK)

                results = self._promote_students(students, current_year, previous_year)
                
                return Response(
                    {"message": _("اكتملت عملية الترقية بنجاح."), "results": results},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        """
        Re-runs promotion for a specific list of students.
        """
        student_ids = request.data.get('student_ids')
        if not student_ids or not isinstance(student_ids, list):
            return Response({"detail": _("يجب توفير قائمة بمعرفات الطلاب (student_ids) في جسم الطلب.")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                try:
                    current_year = AcademicYear.objects.get(is_current=True)
                    previous_year = AcademicYear.objects.filter(end_date__lt=current_year.start_date).order_by('-end_date').first()
                    if not previous_year:
                        return Response({"detail": _("لا يوجد عام دراسي سابق محدد.")}, status=status.HTTP_400_BAD_REQUEST)
                except AcademicYear.DoesNotExist:
                    return Response({"detail": _("لا يوجد عام دراسي حالي محدد.")}, status=status.HTTP_400_BAD_REQUEST)

                students = Student.objects.filter(
                    pk__in=student_ids,
                    section__academic_year=previous_year
                ).select_related('student_class', 'section')

                if not students.exists():
                    return Response({"detail": _("لم يتم العثور على أي طلاب بالمعرفات المحددة في العام الدراسي السابق.")}, status=status.HTTP_404_NOT_FOUND)

                results = self._promote_students(students, current_year, previous_year)
                
                return Response(
                    {"message": _("اكتملت عملية الترقية للطلاب المحددين بنجاح."), "results": results},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class StudentPromotionResetView(APIView):
    permission_classes = [IsAdminOrSuperuser]

    def post(self, request, *args, **kwargs):
        """
        يقوم بحذف جميع سجلات ترقية الطلاب للعام الدراسي السابق.
        """
        try:
            with transaction.atomic():
                try:
                    current_year = AcademicYear.objects.get(is_current=True)
                    previous_year = AcademicYear.objects.filter(end_date__lt=current_year.start_date).order_by('-end_date').first()
                    if not previous_year:
                        return Response({"detail": _("لا يوجد عام دراسي سابق محدد.")}, status=status.HTTP_400_BAD_REQUEST)
                except AcademicYear.DoesNotExist:
                    return Response({"detail": _("لا يوجد عام دراسي حالي محدد.")}, status=status.HTTP_400_BAD_REQUEST)

                # حذف سجلات التقدم والمشاكل المرتبطة بها
                deleted_progressions = StudentProgression.objects.filter(
                    academic_year=current_year
                ).delete()

                return Response(
                    {"message": _("تم إعادة ضبط عملية الترقية بنجاح."), "deleted_records_count": deleted_progressions[0]},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentProgressionIssueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to list and filter student progression issues.
    """
    queryset = StudentProgressionIssue.objects.all()
    serializer_class = StudentProgressionIssueSerializer
    permission_classes = [IsAdminOrSuperuser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StudentProgressionIssueFilterSet
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'student_progression', 
            'student_progression__student', 
            'student_progression__student__user',
            'student_progression__student__student_class',
            'student_progression__student__section',
            'student_progression__academic_year'
        )
        return queryset

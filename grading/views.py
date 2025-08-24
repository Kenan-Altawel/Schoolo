# exams/views.py
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, status , generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q , Avg
from rest_framework import permissions # يجب استيراد permissions
from django.utils.translation import gettext_lazy as _
from accounts.permissions import *
from grading.grade_calculator import GradeCalculator
from .serializers import *
from .models import *
from accounts.models import User 
from teachers.models import Teacher
from students.models import Student 
from classes.models import Section 
from accounts.permissions import CustomPermission
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.views import APIView
from django.db import transaction
from academic.models import AcademicYear, AcademicTerm


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
                teacher = Teacher.objects.get(user=user)
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
            try:
                section = Section.objects.get(id=target_section_id)
                query_params_filters &= (
                    Q(target_section_id=target_section_id) |
                    (Q(target_class_id=section.class_obj_id) & Q(target_section__isnull=True) & Q(stream_type__isnull=True)) |
                    (Q(target_class_id=section.class_obj_id) & Q(stream_type=section.stream_type) & Q(target_section__isnull=True))
                )
            except Section.DoesNotExist:
                pass
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

        # ضبط العام والفصل الحاليين تلقائيًا عند إنشاء الامتحان
        try:
            current_year = AcademicYear.objects.get(is_current=True)
            current_term = AcademicTerm.objects.get(is_current=True, academic_year=current_year)
        except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
            raise ValidationError({
                "detail": _("لا يوجد عام أو فصل دراسي حالي. لا يمكن إنشاء الامتحان بدون تحديد عام وفصل حاليين.")
            })

        serializer.save(academic_year=current_year, academic_term=current_term)

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
        exam_id = self.request.query_params.get('exam_id')
        exam_type = self.request.query_params.get('exam_type')
        target_class_id = self.request.query_params.get('target_class_id')
        target_section_id = self.request.query_params.get('section_id')
        stream_type = self.request.query_params.get('stream_type')


        query_params_filters = Q()

        if subject_id:
            query_params_filters &= Q(exam__subject_id=subject_id)
        if exam_id:
            query_params_filters &= Q(exam_id=exam_id)
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

    

class GradeBulkRecordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, exam_id, section_id, *args, **kwargs):
        """
        إضافة علامات بشكل مجمع لطلاب شعبة معينة في اختبار محدد.
        البيانات المطلوبة في الـ Body:
        {
          "grades": [
            {"student_id": 101, "score": 95.5},
            {"student_id": 102, "score": 88.0},
            ...
          ]
        }
        """
        user = request.user
        grades_data = request.data.get('grades', [])

        if not user.is_teacher():
            return Response(
                {"error": "يجب أن تكون معلماً لإضافة العلامات."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            exam = Exam.objects.get(id=exam_id)
            section = Section.objects.get(id=section_id)
        except Exam.DoesNotExist:
            return Response(
                {"error": "الاختبار غير موجود."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Section.DoesNotExist:
            return Response(
                {"error": "الشعبة غير موجودة."},
                status=status.HTTP_404_NOT_FOUND
            )

        if exam.teacher != user.teacher_profile:
            return Response(
                {"error": "ليس لديك صلاحية لإضافة علامات لهذا الاختبار."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not exam.is_conducted:
            return Response(
                {"error": "لا يمكن إضافة علامات لاختبار لم يتم إجراؤه بعد."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحقق من أن الاختبار يستهدف الشعبة بشكل مباشر أو غير مباشر (عن طريق الصف أو نوع التخصص)
        is_target_section_match = (
            (exam.target_section and exam.target_section == section) or
            (exam.target_section is None and exam.target_class and exam.target_class == section.class_obj and exam.stream_type is None) or
            (exam.target_section is None and exam.target_class and exam.target_class == section.class_obj and exam.stream_type and exam.stream_type == section.stream_type)
        )

        if not is_target_section_match:
            return Response(
                {"error": "الشعبة لا تتوافق مع الأهداف المحددة لهذا الاختبار."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # التأكد من وجود بيانات للعلامات
        if not grades_data:
            return Response(
                {"error": "يجب توفير قائمة العلامات ('grades')."},
                status=status.HTTP_400_BAD_REQUEST
            )

        success_count = 0
        errors = []

        with transaction.atomic():
            for grade_item in grades_data:
                student_id = grade_item.get('student_id')
                score = grade_item.get('score')
                
                if student_id is None or score is None:
                    errors.append({"error": "يجب توفير معرف الطالب والدرجة لكل سجل.", "record": grade_item})
                    continue

                try:
                    student_obj = Student.objects.get(pk=student_id)
                    
                    if student_obj.section != section:
                        errors.append({"error": f"الطالب بالمعرف {student_id} لا ينتمي إلى هذه الشعبة.", "record": grade_item})
                        continue

                    if score > exam.total_marks:
                        errors.append({"error": f"درجة الطالب ({score}) لا يمكن أن تتجاوز الدرجة الكلية ({exam.total_marks}).", "record": grade_item})
                        continue
                    if score < 0:
                        errors.append({"error": f"درجة الطالب ({score}) لا يمكن أن تكون سالبة.", "record": grade_item})
                        continue

                    grade_record, created = Grade.objects.update_or_create(
                        student=student_obj,
                        exam=exam,
                        defaults={
                            'score': score,
                            'graded_at': timezone.now()
                        }
                    )
                    success_count += 1
                except Student.DoesNotExist:
                    errors.append({"error": f"الطالب بالمعرف {student_id} غير موجود.", "record": grade_item})
                except Exception as e:
                    errors.append({"error": str(e), "record": grade_item})

        if errors:
            return Response({
                "message": f"تم تسجيل {success_count} علامة بنجاح. توجد أخطاء في {len(errors)} سجل.",
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response(
            {"message": "تم إضافة جميع العلامات بنجاح.", "count": success_count},
            status=status.HTTP_201_CREATED
        )
    

class SubjectAverageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        student_id = request.query_params.get('student_id')
        subject_id = request.query_params.get('subject_id')
        academic_year_id = request.query_params.get('academic_year_id')
        academic_term_id = request.query_params.get('academic_term_id')

        # الطالب لا يُسمح له بتحديد student_id؛ نستخدم معرفه الذاتي
        if user.is_student():
            try:
                student_id = user.student.pk
            except Student.DoesNotExist:
                return Response({"detail": _("الطالب غير موجود.")}, status=status.HTTP_404_NOT_FOUND)

        if not subject_id:
            return Response({"detail": _("يجب توفير subject_id.")}, status=status.HTTP_400_BAD_REQUEST)
        if not student_id:
            return Response({"detail": _("يجب توفير student_id (لغير الطلاب).")}, status=status.HTTP_400_BAD_REQUEST)

        if not academic_year_id and not academic_term_id:
            try:
                current_year = AcademicYear.objects.get(is_current=True)
                current_term = AcademicTerm.objects.get(is_current=True, academic_year=current_year)
            except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
                return Response({"detail": _("لا يوجد عام أو فصل دراسي حالي.")}, status=status.HTTP_400_BAD_REQUEST)
            academic_year_id = current_year.pk
            academic_term_id = current_term.pk
        elif academic_year_id and academic_term_id:
            try:
                term_obj = AcademicTerm.objects.get(pk=academic_term_id)
            except AcademicTerm.DoesNotExist:
                return Response({"detail": _("الفصل الدراسي غير موجود.")}, status=status.HTTP_404_NOT_FOUND)
            if str(term_obj.academic_year_id) != str(academic_year_id):
                return Response({"detail": _("الفصل المحدد لا ينتمي إلى العام الدراسي المحدد.")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({"detail": _("الطالب غير موجود.")}, status=status.HTTP_404_NOT_FOUND)


        calculator = GradeCalculator()
        avg = calculator.calculate_subject_average(
            student_id=student_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            academic_term_id=academic_term_id,
        )
        return Response({"subject_average": avg})

class OverallAverageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        student_id = request.query_params.get('student_id')
        academic_year_id = request.query_params.get('academic_year_id')
        academic_term_id = request.query_params.get('academic_term_id')

        if user.is_student():
            try:
                student_id = user.student.pk
            except Student.DoesNotExist:
                return Response({"detail": _("الطالب غير موجود.")}, status=status.HTTP_404_NOT_FOUND)
        if not student_id:
            return Response({"detail": _("يجب توفير student_id (لغير الطلاب).")}, status=status.HTTP_400_BAD_REQUEST)

        # المنطق الافتراضي كما في SubjectAverageView
        if not academic_year_id and not academic_term_id:
            try:
                current_year = AcademicYear.objects.get(is_current=True)
                current_term = AcademicTerm.objects.get(is_current=True, academic_year=current_year)
            except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
                return Response({"detail": _("لا يوجد عام أو فصل دراسي حالي.")}, status=status.HTTP_400_BAD_REQUEST)
            academic_year_id = current_year.pk
            academic_term_id = current_term.pk
        elif academic_year_id and academic_term_id:
            try:
                term_obj = AcademicTerm.objects.get(pk=academic_term_id)
            except AcademicTerm.DoesNotExist:
                return Response({"detail": _("الفصل الدراسي غير موجود.")}, status=status.HTTP_404_NOT_FOUND)
            if str(term_obj.academic_year_id) != str(academic_year_id):
                return Response({"detail": _("الفصل المحدد لا ينتمي إلى العام الدراسي المحدد.")}, status=status.HTTP_400_BAD_REQUEST)

        # تحقق الصلاحيات
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({"detail": _("الطالب غير موجود.")}, status=status.HTTP_404_NOT_FOUND)
        if user.is_teacher():
            if hasattr(student.section, 'teacher') and student.section.teacher != user.teacher_profile:
                return Response({"detail": _("ليس لديك الصلاحية لعرض معدل هذا الطالب.")}, status=status.HTTP_403_FORBIDDEN)
        if user.is_student() and student.user != user:
            return Response({"detail": _("ليس لديك الصلاحية لعرض معدلات طالب آخر.")}, status=status.HTTP_403_FORBIDDEN)

        calculator = GradeCalculator()
        avg = calculator.calculate_overall_average(
            student_id=student_id,
            academic_year_id=academic_year_id,
            academic_term_id=academic_term_id,
        )
        return Response({"overall_average": avg})
    

import pandas as pd
import io
import xlsxwriter
from django.http import HttpResponse

class GradeReportViewSet(viewsets.ViewSet):
    """
    ViewSet for generating and downloading Excel reports for grades.
    """
    @action(detail=False, methods=['get'])
    def download_excel_report(self, request):
        student_id = request.query_params.get('student_id')
        section_id = request.query_params.get('section_id')
        subject_id = request.query_params.get('subject_id')
        user = request.user

        if not (student_id or section_id):
            return Response({"error": "يجب توفير معرف الطالب (student_id) أو معرف الشعبة (section_id)."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check permissions
        if not (user.is_superuser or user.is_admin() or user.is_teacher()):
            return Response({"error": "لا تملك الصلاحية للوصول إلى تقارير الدرجات."}, status=status.HTTP_403_FORBIDDEN)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Grades Report')
        bold = workbook.add_format({'bold': True})
        
        # Set report start column for centering
        start_column_index = 3 # Column D

        if student_id:
            # Case 1: All grades for a single student
            try:
                student_obj = Student.objects.get(pk=student_id)
            except Student.DoesNotExist:
                return Response({"error": "الطالب غير موجود."}, status=status.HTTP_404_NOT_FOUND)

            grades_queryset = Grade.objects.filter(student_id=student_id)
            if not grades_queryset.exists():
                return Response({"message": "لا توجد درجات لهذا الطالب."}, status=status.HTTP_200_OK)

            # Write student info
            worksheet.write(1, start_column_index, 'Student Name:', bold)
            worksheet.write(1, start_column_index + 1, student_obj.user.get_full_name())
            worksheet.write(2, start_column_index, 'Section:', bold)
            worksheet.write(2, start_column_index + 1, student_obj.section.name if hasattr(student_obj, 'section') and student_obj.section else "غير محدد")
            
            # Calculate and prepare data
            grade_calculator = GradeCalculator()
            grades_by_subject = {}
            for grade in grades_queryset:
                subject_name = grade.exam.subject.name
                if subject_name not in grades_by_subject:
                    grades_by_subject[subject_name] = []
                grades_by_subject[subject_name].append(grade.score)

            report_data = []
            for subject, grades_list in grades_by_subject.items():
                subject_avg = sum(grades_list) / len(grades_list)
                report_data.append([
                    subject,
                    ', '.join(map(str, grades_list)),
                    f"{subject_avg:.2f}"
                ])
            overall_avg = grade_calculator.calculate_overall_average(student_id=student_id)
            print(overall_avg)
            # Write report data
            headers = ['Subject', 'Grades', 'Subject Average']
            worksheet.write(4, start_column_index, 'Detailed Grades:', bold)
            worksheet.write_row(5, start_column_index, headers, bold)
            
            current_row = 6
            for row in report_data:
                worksheet.write_row(current_row, start_column_index, row)
                current_row += 1

            # Write overall average - Corrected Line
            worksheet.write(current_row + 1, start_column_index, 'Overall Final Average:', bold)
            formatted_avg = f"{overall_avg:.2f}" if overall_avg is not None else "N/A"
            worksheet.write(current_row + 1, start_column_index + 1, formatted_avg)

            filename = f'Student_Grades_Report_{student_obj.user.get_full_name()}.xlsx'

        elif section_id and subject_id:
            # Case 2: Grades for a section in a single subject
            try:
                section_obj = Section.objects.get(pk=section_id)
                subject_obj = Subject.objects.get(pk=subject_id)
            except (Section.DoesNotExist, Subject.DoesNotExist):
                return Response({"error": "الشعبة أو المادة غير موجودة."}, status=status.HTTP_404_NOT_FOUND)

            grades_queryset = Grade.objects.filter(student__section=section_obj, exam__subject=subject_obj).select_related('student__user')
            if not grades_queryset.exists():
                return Response({"message": "لا توجد درجات لطلاب هذه الشعبة في هذه المادة."}, status=status.HTTP_200_OK)

            # Write section and subject info
            worksheet.write(1, start_column_index, 'Class:', bold)
            worksheet.write(1, start_column_index + 1, section_obj.class_obj.name if section_obj.class_obj else "غير محدد")
            worksheet.write(2, start_column_index, 'Section:', bold)
            worksheet.write(2, start_column_index + 1, section_obj.name)
            worksheet.write(3, start_column_index, 'Subject:', bold)
            worksheet.write(3, start_column_index + 1, subject_obj.name)

            # Prepare report data
            report_data = [{'Student Name': grade.student.user.get_full_name(), 'Grade': grade.score} for grade in grades_queryset]
            df_report = pd.DataFrame(report_data)

            # Write report
            worksheet.write_row(5, start_column_index, df_report.columns, bold)
            for row_num, row_data in enumerate(df_report.values):
                worksheet.write_row(row_num + 6, start_column_index, row_data)

            filename = f'Section_Grades_{section_obj.name}_{subject_obj.name}.xlsx'

        elif section_id:
            # Case 3: Overall averages for a section
            try:
                section_obj = Section.objects.get(pk=section_id)
            except Section.DoesNotExist:
                return Response({"error": "الشعبة غير موجودة."}, status=status.HTTP_404_NOT_FOUND)

            students_in_section = Student.objects.filter(section=section_obj)
            if not students_in_section.exists():
                return Response({"message": "لا يوجد طلاب في هذه الشعبة."}, status=status.HTTP_200_OK)

            # Write section info
            worksheet.write(1, start_column_index, 'Class:', bold)
            worksheet.write(1, start_column_index + 1, section_obj.class_obj.name if section_obj.class_obj else "غير محدد")
            worksheet.write(2, start_column_index, 'Section:', bold)
            worksheet.write(2, start_column_index + 1, section_obj.name)

            # Prepare report data
            grade_calculator = GradeCalculator()
            report_data = []
            for student_obj in students_in_section:
                overall_avg = grade_calculator.calculate_overall_average(student_id=student_obj.pk)
                formatted_avg = f"{overall_avg:.2f}" if overall_avg is not None else "N/A"
                report_data.append({
                    'Student Name': student_obj.user.get_full_name(),
                    'Overall Average': formatted_avg
                })
            df_report = pd.DataFrame(report_data)

            # Write report
            worksheet.write_row(4, start_column_index, df_report.columns, bold)
            for row_num, row_data in enumerate(df_report.values):
                worksheet.write_row(row_num + 5, start_column_index, row_data)
                
            filename = f'Section_Averages_Report_{section_obj.name}.xlsx'
        
        else:
             return Response({"error": "الرجاء تحديد معرف الطالب أو الشعبة أو كليهما."}, status=status.HTTP_400_BAD_REQUEST)

        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
from rest_framework import viewsets, permissions
from django.db.models import Q
from academic.models import  AcademicYear, AcademicTerm
from classes.models import Section
from .models import Attendance
from students.models import Student
from .serializers import AttendanceSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Case, When
from rest_framework import status, permissions
import datetime
from rest_framework.decorators import action
from rest_framework import serializers
import io
import pandas as pd
from django.http import HttpResponse
import xlsxwriter

class AttendanceViewSet(viewsets.ModelViewSet):

    """
    مجموعة طرق عرض لإدارة سجلات الحضور.
    """
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.is_admin():
            queryset= Attendance.objects.all()
        
        elif user.is_student():
            try:
                student_obj = Student.objects.get(user=user)
                queryset= Attendance.objects.filter(student=student_obj)
            except Student.DoesNotExist:
                queryset= Attendance.objects.none()
        
        else:
            queryset= Attendance.objects.none()

        filters = Q()

        academic_year_id = self.request.query_params.get('academic_year_id')
        academic_term_id = self.request.query_params.get('academic_term_id')

        # منطق تحديد العام والفصل الدراسي
        if academic_year_id and academic_term_id:
            # إذا تم تحديد الاثنين في الطلب، استخدمهما
            filters &= Q(academic_year_id=academic_year_id)
            filters &= Q(academic_term_id=academic_term_id)
        elif academic_year_id:
            # إذا تم تحديد العام فقط، استخدمه
            filters &= Q(academic_year_id=academic_year_id)
        elif academic_term_id:
            # إذا تم تحديد الفصل فقط، استخدمه
            filters &= Q(academic_term_id=academic_term_id)
        else:
            # إذا لم يتم تحديد أي منهما، استخدم القيم الحالية (is_current=True)
            try:
                current_academic_year = AcademicYear.objects.get(is_current=True)
                current_academic_term = AcademicTerm.objects.get(
                    is_current=True,
                    academic_year=current_academic_year
                )
                filters &= Q(academic_year=current_academic_year, academic_term=current_academic_term)
            except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
                # إذا لم يتم العثور على سنة أو فصل دراسي حالي، لا تُرجع أي بيانات
                return Attendance.objects.none()
        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                date_obj = datetime.date.fromisoformat(date_str)
                # حساب بداية الشهر ونهايته من التاريخ المدخل
                start_date = date_obj.replace(day=1)
                end_date = start_date.replace(month=start_date.month % 12 + 1, day=1) - datetime.timedelta(days=1)
                filters &= Q(date__range=(start_date, end_date))
            except ValueError:
                return Response({"error": "صيغة التاريخ غير صالحة. يجب أن تكون YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        # الفلترة بناءً على student_id (متاحة فقط للادمن)
        student_id = self.request.query_params.get('student_id')
        if student_id and (user.is_superuser or user.is_admin()):
            filters &= Q(student_id=student_id)

        # الفلترة بناءً على date
        day = self.request.query_params.get('day')
        if day:
            filters &= Q(date=day)

        section_id = self.request.query_params.get('section_id')
        if section_id:
            filters &= Q(student__section_id=section_id)
        


        return queryset.filter(filters).distinct()
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {"message": "تم تسجيل  الحضور بنجاح."},
            status=status.HTTP_201_CREATED
        )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {"message": "تم تحديث العنصر بنجاح!"},
            status=status.HTTP_200_OK  
        )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "تم حذف العنصر بنجاح!"},
            status=status.HTTP_204_NO_CONTENT 
        )
    def perform_create(self, serializer):
        user = self.request.user
        if not  (user.is_superuser or user.is_admin()):
            raise permissions.exceptions.PermissionDenied("You must be authenticated to create a record.")

        student = serializer.validated_data.get('student')
        date = serializer.validated_data.get('date')
        status = serializer.validated_data.get('status')
        
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_academic_term = AcademicTerm.objects.filter(is_current=True, academic_year=current_academic_year).first()

        # استخدام update_or_create لتجنب التكرار
        try:
            attendance_record, created = Attendance.objects.update_or_create(
                student=student,
                date=date,
                academic_year=current_academic_year,
                academic_term=current_academic_term,
                defaults={'status': status, 'recorded_by': user}
            )
            if not created:
                # إذا تم تحديث السجل بدلاً من إنشائه
                serializer.instance = attendance_record
        except Exception as e:
            # يمكنك التعامل مع أي أخطاء أخرى هنا
            raise serializers.ValidationError({"error": str(e)})

    def perform_update(self, serializer):
        user = self.request.user
        if not (user.is_superuser or user.is_admin()):
            raise permissions.exceptions.PermissionDenied("You must be authenticated to create a record.")

        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_academic_term = AcademicTerm.objects.filter(is_current=True, academic_year=current_academic_year).first()

        serializer.save(
            recorded_by=user,
            academic_year=current_academic_year,
            academic_term=current_academic_term
        )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user
        student_id = request.query_params.get('student_id')
        
        
        if user.is_superuser or user.is_admin():
            try:
                student_obj = Student.objects.get(pk=student_id)
                queryset = Attendance.objects.filter(student=student_obj)
            except Student.DoesNotExist:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        
        elif user.is_student():
            try:
                student_obj = Student.objects.get(user=user)
                queryset = Attendance.objects.filter(student=student_obj)
            except Student.DoesNotExist:
                return Response({"error": "الطالب غير موجود."}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({"error": "You do not have permission to view this content."}, status=status.HTTP_403_FORBIDDEN)

        # تطبيق الفلترات الإضافية من معلمات الاستعلام
        filters = Q()
        # date = self.request.query_params.get('date')
        # if date:
        #     filters &= Q(date=date)
        
        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                date_obj = datetime.date.fromisoformat(date_str)
                # حساب بداية الشهر ونهايته من التاريخ المدخل
                start_date = date_obj.replace(day=1)
                end_date = start_date.replace(month=start_date.month % 12 + 1, day=1) - datetime.timedelta(days=1)
                filters &= Q(date__range=(start_date, end_date))
            except ValueError:
                return Response({"error": "صيغة التاريخ غير صالحة. يجب أن تكون YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        academic_year_id = self.request.query_params.get('academic_year_id')
        academic_term_id = self.request.query_params.get('academic_term_id')
        
        if academic_year_id:
            filters &= Q(academic_year_id=academic_year_id)
        if academic_term_id:
            filters &= Q(academic_term_id=academic_term_id)
        
        queryset = queryset.filter(filters)

        # حساب إحصائيات الحضور
        stats = queryset.aggregate(
            present_count=Count(Case(When(status='present', then=1))),
            absent_count=Count(Case(When(status='absent', then=1))),
            late_count=Count(Case(When(status='late', then=1))),
            excused_count=Count(Case(When(status='excused', then=1))),
            total_count=Count('id')
        )
        total = stats['total_count'] or 0

        # حساب النسب المئوية
        percentages = {
            "present": (stats['present_count'] / total) * 100 if total > 0 else 0,
            "absent": (stats['absent_count'] / total) * 100 if total > 0 else 0,
            "late": (stats['late_count'] / total) * 100 if total > 0 else 0,
            "excused": (stats['excused_count'] / total) * 100 if total > 0 else 0,
        }

        return Response({
            "counts": {
                "present": stats['present_count'] or 0,
                "absent": stats['absent_count'] or 0,
                "late": stats['late_count'] or 0,
                "excused": stats['excused_count'] or 0,
                "total": total
            },
            "percentages": percentages
        })

    @action(detail=False, methods=['get'])
    def download_excel_report(self, request):
        student_id = request.query_params.get('student_id')
        section_id = request.query_params.get('section_id')
        user = request.user
        
        if not (student_id or section_id):
            return Response({"error": "يجب توفير معرف الطالب (student_id) أو معرف الشعبة (section_id)."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not (user.is_superuser or user.is_admin()):
            if student_id:
                try:
                    student_obj = Student.objects.get(user=user)
                    if str(student_obj.pk) != student_id:
                        return Response({"error": "لا تملك الصلاحية للوصول إلى هذا التقرير."}, status=status.HTTP_403_FORBIDDEN)
                except Student.DoesNotExist:
                    return Response({"error": "الطالب غير موجود."}, status=status.HTTP_404_NOT_FOUND)
            elif section_id:
                return Response({"error": "لا تملك الصلاحية للوصول إلى هذا التقرير."}, status=status.HTTP_403_FORBIDDEN)
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Attendance Report')
        bold = workbook.add_format({'bold': True})

        # تحديد العمود الذي سيبدأ منه التقرير ليظهر في المنتصف
        start_column_index = 3 # العمود D

        if student_id:
            try:
                student_obj = Student.objects.get(pk=student_id)
            except Student.DoesNotExist:
                return Response({"error": "الطالب غير موجود."}, status=status.HTTP_404_NOT_FOUND)
            
            queryset = self.get_queryset().filter(student_id=student_id).order_by('date')
            if not queryset.exists():
                return Response({"message": "لا توجد سجلات حضور لهذا الطالب."}, status=status.HTTP_200_OK)
            
            # كتابة معلومات الطالب العامة
            worksheet.write(1, start_column_index, 'Student Name:', bold)
            worksheet.write(1, start_column_index + 1, student_obj.user.get_full_name())
            worksheet.write(2, start_column_index, 'Student Enrollment Number:', bold)
            worksheet.write(2, start_column_index + 1, student_obj.enrollment_number)
            worksheet.write(3, start_column_index, 'Class:', bold)
            worksheet.write(3, start_column_index + 1, student_obj.student_class.name if hasattr(student_obj, 'student_class') and student_obj.student_class else "غير محدد")
            worksheet.write(4, start_column_index, 'Section:', bold)
            worksheet.write(4, start_column_index + 1, student_obj.section.name if hasattr(student_obj, 'section') and student_obj.section else "غير محدد")
            
            # حساب الإحصائيات
            stats = queryset.aggregate(
                present_count=Count(Case(When(status='present', then=1))),
                absent_count=Count(Case(When(status='absent', then=1))),
                late_count=Count(Case(When(status='late', then=1))),
                excused_count=Count(Case(When(status='excused', then=1))),
                total_count=Count('id')
            )
            total = stats['total_count'] or 0
            
            percentages = {
                "present": (stats['present_count'] / total) * 100 if total > 0 else 0,
                "absent": (stats['absent_count'] / total) * 100 if total > 0 else 0,
                "late": (stats['late_count'] / total) * 100 if total > 0 else 0,
                "excused": (stats['excused_count'] / total) * 100 if total > 0 else 0,
            }

            # كتابة جدول الملخص
            summary_data = {
                'Status': ['Present', 'Absent', 'Late', 'Excused', 'Total'],
                'Count': [stats['present_count'], stats['absent_count'], 
                          stats['late_count'], stats['excused_count'], total],
                'Percentage': [f"{percentages['present']:.2f}%", f"{percentages['absent']:.2f}%", 
                               f"{percentages['late']:.2f}%", f"{percentages['excused']:.2f}%", '100.00%']
            }
            df_summary = pd.DataFrame(summary_data)
            worksheet.write(6, start_column_index, 'Attendance Summary:', bold)
            worksheet.write_row(7, start_column_index, df_summary.columns, bold)
            for row_num, row_data in enumerate(df_summary.values):
                worksheet.write_row(row_num + 8, start_column_index, row_data)

            # جلب البيانات التفصيلية للتقرير
            data = list(queryset.values(
                'date', 'status', 'academic_year__name', 'academic_term__name'
            ))

            df_report = pd.DataFrame(data)
            report_start_row = 15
            df_report.rename(columns={'date': 'Date', 'status': 'Status', 'academic_year__name': 'Academic Year', 'academic_term__name': 'Academic Term'}, inplace=True)
            worksheet.write(report_start_row - 2, start_column_index, 'Detailed Report:', bold)
            worksheet.write_row(report_start_row, start_column_index, df_report.columns, bold)
            for row_num, row_data in enumerate(df_report.values):
                row_data_str = [str(item) for item in row_data]
                worksheet.write_row(row_num + report_start_row + 1, start_column_index, row_data_str)
            
            filename = f'Student_Attendance_Report_{student_obj.user.get_full_name()}.xlsx'

        elif section_id:
            try:
                section_obj = Section.objects.get(pk=section_id)
                student_class_obj = section_obj.class_obj
            except Section.DoesNotExist:
                return Response({"error": "الشعبة غير موجودة."}, status=status.HTTP_404_NOT_FOUND)

            # كتابة معلومات الصف والشعبة العامة في الأعلى
            worksheet.write(1, start_column_index, 'Class:', bold)
            worksheet.write(1, start_column_index + 1, student_class_obj.name if student_class_obj else "غير محدد")
            worksheet.write(2, start_column_index, 'Section:', bold)
            worksheet.write(2, start_column_index + 1, section_obj.name)

            students_in_section = Student.objects.filter(section=section_obj)
            if not students_in_section.exists():
                return Response({"message": "لا يوجد طلاب في هذه الشعبة."}, status=status.HTTP_200_OK)
            
            # تحديد سطر بداية الجدول
            current_row = 5
            
            # كتابة رأس الجدول
            headers = ['Student Name', 'Present %', 'Absent %', 'Late %', 'Excused %']
            worksheet.write_row(current_row, start_column_index, headers, bold)
            current_row += 1

            for student_obj in students_in_section:
                queryset = self.get_queryset().filter(student=student_obj).order_by('date')
                
                stats = queryset.aggregate(
                    present_count=Count(Case(When(status='present', then=1))),
                    absent_count=Count(Case(When(status='absent', then=1))),
                    late_count=Count(Case(When(status='late', then=1))),
                    excused_count=Count(Case(When(status='excused', then=1))),
                    total_count=Count('id')
                )
                total = stats['total_count'] or 0
                
                percentages = {
                    "present": (stats['present_count'] / total) * 100 if total > 0 else 0,
                    "absent": (stats['absent_count'] / total) * 100 if total > 0 else 0,
                    "late": (stats['late_count'] / total) * 100 if total > 0 else 0,
                    "excused": (stats['excused_count'] / total) * 100 if total > 0 else 0,
                }
                
                # إعداد البيانات لسطر واحد
                row_data = [
                    student_obj.user.get_full_name(),
                    f"{percentages['present']:.2f}%",
                    f"{percentages['absent']:.2f}%",
                    f"{percentages['late']:.2f}%",
                    f"{percentages['excused']:.2f}%",
                ]
                
                worksheet.write_row(current_row, start_column_index, row_data)
                current_row += 1
            
            filename = f'Section_Attendance_Report_{section_obj.name}.xlsx'

        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

class AttendanceBulkRecordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, section_id, date_str, *args, **kwargs):
        """
        تسجيل الحضور بشكل مجمع لشعبة في تاريخ معين.
        البيانات المطلوبة في الـ Body:
        {
          "students_attendance": [
            {"student_id": 101, "status": "present"},
            {"student_id": 102, "status": "absent"},
            ...
          ]
        }
        """
        user = request.user
        students_attendance = request.data.get('students_attendance', [])

        # التأكد من أن المستخدم لديه صلاحية التسجيل
        if not (user.is_superuser or user.is_admin() ):
            return Response(
                {"error": "You do not have permission to record attendance."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # التحقق من البيانات المرسلة
        if not students_attendance:
            return Response(
                {"error": "يجب توفير حالة الحضور للطلاب."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date_obj = datetime.date.fromisoformat(date_str)
            section_obj = Section.objects.get(id=section_id)
        except (ValueError, Section.DoesNotExist):
            return Response(
                {"error": "صيغة التاريخ أو معرف الشعبة غير صالح."},
                status=status.HTTP_400_BAD_REQUEST
            )


        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_academic_term = AcademicTerm.objects.filter(is_current=True, academic_year=current_academic_year).first()

        success_count = 0
        errors = []

        # حلقة على كل طالب في القائمة
        for student_record in students_attendance:
            student_id = student_record.get('student_id')
            attendance_status  = student_record.get('status')
            
            if not student_id or not status:
                errors.append({"error": "يجب توفير معرف الطالب والحالة لكل سجل.", "record": student_record})
                continue
            
            try:
                student_obj = Student.objects.get(pk=student_id)
                
                # استخدام update_or_create لتجنب التكرار ولتحديث السجل إذا كان موجوداً
                attendance_record, created = Attendance.objects.update_or_create(
                    student=student_obj,
                    date=date_obj,
                    defaults={
                        'status': attendance_status ,
                        'recorded_by': user,
                        'academic_year': current_academic_year,
                        'academic_term': current_academic_term
                    }
                )
                success_count += 1
            except Student.DoesNotExist:
                errors.append({"error": f"الطالب بالمعرف {student_id} غير موجود.", "record": student_record})
            except Exception as e:
                errors.append({"error": str(e), "record": student_record})
        
        if errors:
            return Response({
                "message": f"تم تسجيل {success_count} سجل بنجاح. توجد أخطاء في {len(errors)} سجل.",
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response(
            {"message": "تم تسجيل جميع سجلات الحضور بنجاح.", "count": success_count},
            status=status.HTTP_201_CREATED
        )
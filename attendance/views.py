from rest_framework import viewsets, permissions
from django.db.models import Q
from academic.models import  AcademicYear, AcademicTerm
from .models import Attendance
from students.models import Student
from .serializers import AttendanceSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Case, When
from rest_framework import status, permissions

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
        if not academic_year_id and not academic_term_id:
            try:
                current_academic_year = AcademicYear.objects.get(is_current=True)
                current_academic_term = AcademicTerm.objects.get(
                    is_current=True,
                    academic_year=current_academic_year
                )
                filters &= Q(academic_year=current_academic_year, academic_term=current_academic_term)
            except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
                return Attendance.objects.none()
            else:
                if academic_year_id:
                    filters &= Q(academic_year_id=academic_year_id)
                if academic_term_id:
                    filters &= Q(academic_term_id=academic_term_id)

            student_id = self.request.query_params.get('student_id')
            if student_id and (user.is_superuser or user.is_admin()):
                filters &= Q(student_id=student_id)

            date = self.request.query_params.get('date')
            if date:
                filters &= Q(date=date)

            return queryset.filter(filters).distinct()
        

    def perform_create(self, serializer):
        user = self.request.user
        if not  (user.is_superuser or user.is_admin()):
            raise permissions.exceptions.PermissionDenied("You must be authenticated to create a record.")

        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_academic_term = AcademicTerm.objects.filter(is_current=True, academic_year=current_academic_year).first()

        serializer.save(
            recorded_by=user,
            academic_year=current_academic_year,
            academic_term=current_academic_term
        )
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

class AttendanceSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        student_id = request.query_params.get('student_id')
        
        # تحديد الـ queryset الأساسي بناءً على دور المستخدم
        if user.is_superuser or user.is_admin():
            queryset = Attendance.objects.all()
        
        elif user.is_student():
            try:
                student_obj = Student.objects.get(user=user)
                queryset = Attendance.objects.filter(student=student_obj)
            except Student.DoesNotExist:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
            if student_id and str(student_obj.id) != student_id:
                return Response({"error": "You can only view your own attendance summary."}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"error": "You do not have permission to view this content."}, status=status.HTTP_403_FORBIDDEN)

        # تطبيق الفلترات الإضافية من معلمات الاستعلام
        filters = Q()
        date = self.request.query_params.get('date')
        if date:
            filters &= Q(date=date)
        
        academic_year_id = self.request.query_params.get('academic_year_id')
        academic_term_id = self.request.query_params.get('academic_term_id')
        
        if academic_year_id:
            filters &= Q(academic_year_id=academic_year_id)
        if academic_term_id:
            filters &= Q(academic_term_id=academic_term_id)
        
        # تطبيق الفلترة على الـ queryset
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
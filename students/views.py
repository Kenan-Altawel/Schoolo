# students/views.py (أو حيث تضع Views الطلاب)

from django.shortcuts import get_object_or_404
from rest_framework import generics ,status
from academic.models import AcademicTerm, AcademicYear
from accounts.permissions import *
from rest_framework.permissions import AllowAny
from schedules.models import ClassSchedule
from teachers.models import Teacher
from .models import Student 
from .serializers import *
from classes.models import Class
from accounts.models import User
from rest_framework.exceptions import PermissionDenied

class PendingStudentList(generics.ListAPIView):
    """
    يعرض قائمة بجميع طلبات تسجيل الطلاب المعلقة (التي لم يتم قبولها بعد).
    فقط للمستخدمين الإداريين.
    """
    serializer_class = PendingStudentApplicationSerializer
    permission_classes = [IsAdminOrSuperuser] 

    def get_queryset(self):
        queryset = Student.objects.filter(user__is_active=False)
        student_status = self.request.query_params.get('student_status', None)
        if student_status:
            valid_statuses = [choice[0] for choice in Student.STUDENT_STATUS_CHOICES]
            if student_status in valid_statuses:
                queryset = queryset.filter(student_status=student_status)

        queryset = Student.objects.filter(user__is_active=False)
        register_status = self.request.query_params.get('register_status', None)
        if register_status:
            valid_statuses = [choice[0] for choice in Student.STUDENT_register_CHOICES]
            if register_status in valid_statuses:
                queryset = queryset.filter(register_status=register_status)
           
        class_id = self.request.query_params.get('student_class', None)
        if class_id:
            try:
                class_id = int(class_id)
                if Class.objects.filter(id=class_id).exists():
                    queryset = queryset.filter(student_class__id=class_id)
            except ValueError:
                pass
        queryset = queryset.select_related('user', 'student_class', 'section')

        return queryset


from rest_framework.exceptions import  ValidationError 
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.response import Response

User = get_user_model()

class ApproveStudentAPIView(generics.UpdateAPIView):
    serializer_class = StudentAcceptanceSerializer
    permission_classes = [IsAdminOrSuperuser] 
    lookup_field = 'user_id' 

    def get_queryset(self):
        return Student.objects.all().select_related('user', 'student_class')

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        student = get_object_or_404(self.get_queryset(), user__id=user_id)
        if student.register_status != 'pending':
            raise ValidationError(
                {"detail": f"الطالب (ID: {user_id}) حالته '{student.register_status}' ولا يمكن قبوله/رفضه من هذه الواجهة. يجب أن تكون حالته 'pending'."}
            )
            
        return student

    def update(self, request, *args, **kwargs):
        student = self.get_object() 
        serializer = self.get_serializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        student = serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ManagerAddStudentAPIView(generics.CreateAPIView):
    serializer_class = ManagerStudentCreationSerializer
    permission_classes = [IsAdminOrSuperuser]

    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_instance = serializer.save()
        
        response_data = {
            "message": "students added successfully",
            "student_data": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    

class IsManagerOrTeacher(permissions.BasePermission):
    """
    صلاحية تسمح بالوصول فقط للمديرين والمشرفين والأساتذة.
    """
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_superuser or user.is_admin() or user.is_teacher())

class StudentListAPIView(generics.ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = [IsManagerOrTeacher]

class StudentListAPIView(generics.ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = [IsManagerOrTeacher]

    def get_queryset(self):
        user = self.request.user
        section_id_param = self.request.query_params.get('section_id')
        
        # دائماً نبدأ بـ QuerySet يحتوي فقط على الطلاب النشطين
        queryset = Student.objects.filter(user__is_active=True)

        # التحقق من دور المستخدم وتطبيق الفلاتر المناسبة
        if user.is_superuser or user.is_admin():
            # إذا كان المستخدم مديراً أو مشرفاً
            class_id_param = self.request.query_params.get('class_id')
            
            if section_id_param:
                queryset = queryset.filter(section_id=section_id_param)
            elif class_id_param:
                queryset = queryset.filter(student_class_id=class_id_param)
            
        elif user.is_teacher():
            try:
                teacher_instance = Teacher.objects.get(user=user)
                current_academic_year = AcademicYear.objects.get(is_current=True)
                current_academic_term = AcademicTerm.objects.get(is_current=True, academic_year=current_academic_year)
                
                # جلب الشعب التي يدرسها الأستاذ في العام والفصل الدراسي الحالي
                sections_taught_ids = ClassSchedule.objects.filter(
                    teacher=teacher_instance,
                    academic_year=current_academic_year,
                    academic_term=current_academic_term
                ).values_list('section_id', flat=True).distinct()
                
                if section_id_param:
                    if int(section_id_param) in sections_taught_ids:
                        queryset = queryset.filter(section_id=section_id_param)
                    else:
                        raise PermissionDenied("ليس لديك الصلاحية لعرض طلاب هذا القسم.")
                else:
                    queryset = queryset.filter(section_id__in=sections_taught_ids)
                    
            except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
                queryset = Student.objects.none()
            except AttributeError:
                queryset = Student.objects.none()
        
        return queryset.select_related('user', 'student_class', 'section')
    

class StudentProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileUpdateSerializer
    permission_classes = [IsStudent]
    
    def get_object(self):
        return self.request.user.student

    def perform_update(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"detail": "تم تحديث البيانات بنجاح"}, status=status.HTTP_200_OK)


class ManagerStudentUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = ManagerStudentUpdateSerializer
    permission_classes = [ IsAdminOrSuperuser]

    def perform_update(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"detail": "تم تحديث بيانات الطالب بنجاح"}, status=status.HTTP_200_OK)

class ManagerStudentDeleteView(generics.DestroyAPIView):
    queryset = Student.objects.all()
    permission_classes = [IsAdminOrSuperuser]

    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user = instance.user
            instance.delete()
            user.delete()
            
            return Response({"detail": "تم حذف الطالب بنجاح"}, status=status.HTTP_204_NO_CONTENT)
        
        except Student.DoesNotExist:
            return Response({"detail": "الطالب غير موجود"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"detail": f"حدث خطأ أثناء الحذف: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
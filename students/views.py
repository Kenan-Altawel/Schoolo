# students/views.py (أو حيث تضع Views الطلاب)

from django.shortcuts import get_object_or_404
from rest_framework import generics ,status
from accounts.permissions import *
from .models import Student 
from .serializers import PendingStudentApplicationSerializer ,StudentAcceptanceSerializer
from classes.models import Class
from accounts.models import User
class PendingStudentList(generics.ListAPIView):
    """
    يعرض قائمة بجميع طلبات تسجيل الطلاب المعلقة (التي لم يتم قبولها بعد).
    فقط للمستخدمين الإداريين.
    """
    serializer_class = PendingStudentApplicationSerializer
    permission_classes = [IsAdminOrSuperuser] 

    def get_queryset(self):
        queryset = Student.objects.filter(user__is_active=False)
        student_status = self.request.query_params.get('status', None)
        if student_status:
            valid_statuses = [choice[0] for choice in Student.STUDENT_STATUSSTUDENTS_CHOICES]
            if student_status in valid_statuses:
                queryset = queryset.filter(status=student_status)
           
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
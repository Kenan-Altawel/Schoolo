# teachers/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
from .serializers import *
from .models import Teacher ,TeacherAvailability
from django.shortcuts import get_object_or_404 
import logging
from rest_framework import permissions
from accounts.permissions import *
from subject.models import TeacherSubject
from .filters import TeacherFilter
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

class CustomPermission(permissions.BasePermission):
   
    def has_permission(self, request, view):
        return IsAdminOrSuperuser().has_permission(request, view)


logger = logging.getLogger(__name__)

class IsOwnerOfTeacherProfile(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class TeacherProfileUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherProfileUpdateSerializer
    permission_classes = [IsOwnerOfTeacherProfile] 

    def get_object(self):
        
        return get_object_or_404(Teacher, user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False) 
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer) 

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"Teacher profile for user {self.request.user.phone_number} updated.")

class TeacherAvailabilityListAPIView(generics.ListAPIView):
    serializer_class = TeacherAvailabilitySerializer
    permission_classes = [permissions.AllowAny] 

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        if teacher_id:
            return TeacherAvailability.objects.filter(teacher_id=teacher_id)
        return TeacherAvailability.objects.none()
    
    
class TeacherListView(generics.ListAPIView):
    permission_classes = [CustomPermission] 
    queryset = Teacher.objects.all()
    filterset_class = TeacherFilter
    filter_backends = [DjangoFilterBackend] 
    serializer_class = TeacherListSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['specialization', 'user__first_name', 'user__last_name']
    ordering = ['user__first_name']

class TeacherDetailView(generics.RetrieveAPIView):
    permission_classes = [CustomPermission]
    queryset = Teacher.objects.all()
    serializer_class = TeacherListSerializer
    lookup_field = 'pk'
    
class TeacherSubjectsListView(generics.ListAPIView):
    serializer_class = TeacherSubjectSerializer
    permission_classes = [CustomPermission] 
    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        return TeacherSubject.objects.filter(teacher_id=teacher_id)
    

class ManagerTeacherUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = ManagerTeacherUpdateSerializer
    permission_classes = [IsAdminOrSuperuser]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"detail": "تم تحديث بيانات المستخدم بنجاح"}, status=status.HTTP_200_OK)
    

class ManagerTeacherDeleteView(generics.DestroyAPIView):
    queryset = Teacher.objects.all()
    permission_classes = [IsAdminOrSuperuser]
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user = instance.user
            instance.delete()
            user.delete()
            
            return Response({"detail": "تم حذف المستخدم بنجاح"}, status=status.HTTP_204_NO_CONTENT)
        
        except Teacher.DoesNotExist:
            return Response({"detail": "المستخدم غير موجود"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"detail": f"حدث خطأ أثناء الحذف: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
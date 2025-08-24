from django.shortcuts import render
from accounts.permissions import  IsSuperuser
from .serializers import *
from .models import Admin
from rest_framework import generics, status
from rest_framework.response import Response
from .filters import TeacherFilter
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

class ManagerAdminUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Admin.objects.all()
    serializer_class = ManagerAdminUpdateSerializer
    permission_classes = [IsSuperuser]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"detail": "تم تحديث بيانات المعلم بنجاح"}, status=status.HTTP_200_OK)
    

class ManagerAdminDeleteView(generics.DestroyAPIView):
    queryset = Admin.objects.all()
    permission_classes = [IsSuperuser]

    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user = instance.user
            instance.delete()
            user.delete()
            
            return Response({"detail": "تم حذف بنجاح"}, status=status.HTTP_204_NO_CONTENT)
        
        except Admin.DoesNotExist:
            return Response({"detail": " غير موجود"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"detail": f"حدث خطأ أثناء الحذف: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
class AdminListView(generics.ListAPIView):
    permission_classes = [IsSuperuser] 
    queryset = Admin.objects.all()
    filterset_class = TeacherFilter
    filter_backends = [DjangoFilterBackend] 
    serializer_class = AdminListSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['specialization', 'user__first_name', 'user__last_name']
    ordering = ['user__first_name']

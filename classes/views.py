from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions 
from .models import Class, Section
from .serializers import ClassSerializer, SectionSerializer
from accounts.permissions import *
from django_filters.rest_framework import DjangoFilterBackend
from .filters import *
from rest_framework.permissions import AllowAny
          
class CustomPermission(permissions.BasePermission):
   
    def has_permission(self, request, view):
        if not request.user :
            return False

        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return IsAdminOrSuperuser().has_permission(request, view)

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [CustomPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClassFilter

    @action(detail=True, methods=['GET'], url_path='show-sections', serializer_class=SectionSerializer)
    def list_sections(self, request, pk=None):
        
        class_obj = self.get_object() 
        sections = class_obj.sections.all() 
        serializer = self.get_serializer(sections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
   
    @action(detail=True, methods=['post'], url_path='sections', serializer_class=SectionSerializer)
    def create_section(self, request, pk=None):
        class_obj = self.get_object() 
        serializer = self.get_serializer(data=request.data,many=True, context={'request': request, 'class_obj': class_obj})
        serializer.is_valid(raise_exception=True)
        serializer.save() 
        return Response(serializer.data, status=status.HTTP_201_CREATED)

   
    
class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [CustomPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SectionFilter
    
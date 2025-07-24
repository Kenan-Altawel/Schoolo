from django.shortcuts import render
from rest_framework import viewsets
from .models import *
from accounts.permissions import *
from .serializers import AcademicYearSerializer, AcademicTermSerializer
from .serializers import TimeSlotSerializer, DayOfWeekSerializer
from rest_framework.response import Response
from rest_framework import status

class CustomPermission(permissions.BasePermission):
   
    def has_permission(self, request, view):
        if not request.user :
            return False

        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return IsAdminOrSuperuser().has_permission(request, view)

class AcademicYearViewSet(viewsets.ModelViewSet):
    permission_classes = [CustomPermission]
    serializer_class = AcademicYearSerializer

    def get_queryset(self):
        queryset = AcademicYear.objects.all() 
        is_current_param = self.request.query_params.get('is_current', None)
        if is_current_param and is_current_param.lower() == 'true':
            queryset = queryset.filter(is_current=True)
            
        return queryset

class AcademicTermViewSet(viewsets.ModelViewSet):
    permission_classes = [CustomPermission]
    serializer_class = AcademicTermSerializer

    def get_queryset(self):
        queryset = AcademicTerm.objects.all()
        academic_year_id = self.request.query_params.get('year_id', None)
        if academic_year_id:
            queryset = queryset.filter(academic_year__id=academic_year_id)
        
        academic_year_name = self.request.query_params.get('year_name', None)
        if academic_year_name:
            queryset = queryset.filter(academic_year__name__iexact=academic_year_name) # iexact لتجاهل حالة الأحرف
            
        return queryset


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [CustomPermission]

class DayOfWeekViewSet(viewsets.ModelViewSet):
    queryset = DayOfWeek.objects.all()
    serializer_class = DayOfWeekSerializer
    permission_classes = [CustomPermission]
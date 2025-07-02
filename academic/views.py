from django.shortcuts import render
from rest_framework import viewsets
from .models import *
from accounts.permissions import *
from .serializers import AcademicYearSerializer, AcademicTermSerializer
from .serializers import TimeSlotSerializer, DayOfWeekSerializer
from rest_framework.response import Response
from rest_framework import status

class AcademicYearViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperuser]
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer

class AcademicTermViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperuser]
    queryset = AcademicTerm.objects.all()
    serializer_class = AcademicTermSerializer


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAdminOrSuperuser]

class DayOfWeekViewSet(viewsets.ModelViewSet):
    queryset = DayOfWeek.objects.all()
    serializer_class = DayOfWeekSerializer
    permission_classes = [IsAdminOrSuperuser]
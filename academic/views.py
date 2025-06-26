from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import AcademicYear, AcademicTerm
from .serializers import AcademicYearSerializer, AcademicTermSerializer
from rest_framework.response import Response
from rest_framework import status


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if  request.user and request.user.is_superuser:
            return True    

class AcademicYearViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsSuperUser]
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer

class AcademicTermViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsSuperUser]
    queryset = AcademicTerm.objects.all()
    serializer_class = AcademicTermSerializer
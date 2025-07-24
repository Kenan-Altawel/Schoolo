# teachers/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
from .serializers import TeacherProfileUpdateSerializer
from .models import Teacher 
from django.shortcuts import get_object_or_404 
import logging

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
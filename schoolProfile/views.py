from rest_framework import generics, permissions
from .models import SchoolProfile
from .serializers import SchoolProfileSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_admin() or request.user.is_superuser)

class SchoolProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = SchoolProfileSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self):
        obj, _ = SchoolProfile.objects.get_or_create(pk=1)
        return obj 
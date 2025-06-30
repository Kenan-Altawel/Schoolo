from rest_framework.permissions import BasePermission
from admins.models import Admin

class IsAdminUserOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            isinstance(request.user, Admin) and
            request.user.is_authenticated
        )
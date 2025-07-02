# accounts/permissions.py
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsAdmin(permissions.BasePermission):
    """
    يسمح بالوصول فقط للمستخدمين الذين ينتمون إلى مجموعة 'Manager'.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_admin()

class IsTeacher(permissions.BasePermission):
    """
    يسمح بالوصول فقط للمستخدمين الذين ينتمون إلى مجموعة 'Teacher'.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_teacher()

class IsStudent(permissions.BasePermission):
    """
    يسمح بالوصول فقط للمستخدمين الذين ينتمون إلى مجموعة 'Student'.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_student()

class IsSuperuser(permissions.BasePermission):
    """
    يسمح بالوصول فقط للمستخدمين الذين يملكون صلاحيات superuser في النظام.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser

class IsAdminOrSuperuser(permissions.BasePermission):
    """
    يسمح بالوصول فقط للمستخدمين الذين ينتمون إلى مجموعة 'Manager' أو superuser.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
       
        return request.user.is_admin() or request.user.is_superuser
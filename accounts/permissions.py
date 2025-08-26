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
    
class CustomPermission(permissions.BasePermission):
   
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True
        
        else:
            return IsAdminOrSuperuser().has_permission(request, view)

class IsAuthenticatedAndTeacherForWrites(permissions.BasePermission):
   
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        else:
            return IsTeacher().has_permission(request, view)
        

class GradePermissions(permissions.BasePermission):
    """
    يحدد الصلاحيات على نموذج العلامات (Grade) بناءً على دور المستخدم ونوع العملية.
    
    - عرض (GET): متاح لجميع المستخدمين الموثقين.
    - إضافة (POST): متاح للمدرسين فقط.
    - تعديل/حذف (PUT/PATCH/DELETE): متاح للمديرين/المشرفين فقط.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if view.action == 'create':
            return request.user.is_teacher()
        
        if view.action in ['update', 'partial_update', 'destroy']:
            return request.user.is_admin() or request.user.is_superuser
        
        return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
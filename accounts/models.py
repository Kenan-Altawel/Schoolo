from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from django.conf import settings # لاستخدام AUTH_USER_MODEL في OTP
from django.utils import timezone # للتعامل مع الوقت
from datetime import timedelta
import random
import string

class AutoCreateAndAutoUpdateTimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ آخر تحديث"))

    class Meta:
        abstract = True

class UserManager(BaseUserManager):
    def _create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_student_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False) 

        user = self._create_user(phone_number, password, **extra_fields)
        Group.objects.get(name='Student').custom_user_groups.add(user)
        return user

    def create_teacher_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False) 
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False) 
        user = self._create_user(phone_number, password, **extra_fields)
        Group.objects.get(name='Teacher').custom_user_groups.add(user)
        return user
    
    def create_admin_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False) 
        user = self._create_user(phone_number, password, **extra_fields)
        Group.objects.get(name='Manager').custom_user_groups.add(user)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_phone_verified', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self._create_user(phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin , AutoCreateAndAutoUpdateTimeStampedModel):
    phone_number = models.CharField(max_length=10, unique=True, verbose_name=_('رقم الهاتف'))
    first_name = models.CharField(max_length=150, blank=True, verbose_name=_('الاسم الأول'))
    last_name = models.CharField(max_length=150, blank=True, verbose_name=_('الاسم الأخير')) 
    is_active = models.BooleanField(default=False, verbose_name=_('نشط')) 
    is_staff = models.BooleanField(default=False, verbose_name=_('موظف'))
    is_superuser = models.BooleanField(default=False, verbose_name=_('مشرف'))
    last_login = models.DateTimeField(null=True, blank=True, verbose_name=_('آخر تسجيل دخول')) 
    is_phone_verified = models.BooleanField(default=False, verbose_name=_("تم تأكيد رقم الهاتف"))
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to. A user will get all permissions '
                    'granted to each of their groups.'),
        related_name="custom_user_groups", 
        related_query_name="custom_user_query",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', # يشير إلى موديل Permission الافتراضي
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions", 
        related_query_name="custom_user_permission_query",
    )
    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = [] # يمكنك إضافة 'first_name', 'last_name' هنا إذا أردتها مطلوبة عند create_superuser

    class Meta:
        verbose_name = _('المستخدم')
        verbose_name_plural = _('المستخدمون')

    def __str__(self):
        return self.phone_number

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name
    

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return self.is_active and self.is_superuser
    
    def is_student(self):
        return self.groups.filter(name='Student').exists() 

    def is_teacher(self):
        return self.groups.filter(name='Teacher').exists() 

    def is_admin(self):
        return self.groups.filter(name='Manager').exists() 
    
    
class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk: 
            if not self.code:
                self.code = ''.join(random.choices(string.digits, k=6))
            if not self.expires_at:
                self.expires_at = timezone.now() + timedelta(minutes=10) 
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    class Meta:
        verbose_name = _("رمز OTP")
        verbose_name_plural = _("رموز OTP")

    def __str__(self):
        return f"OTP for {self.user.phone_number}: {self.code}"
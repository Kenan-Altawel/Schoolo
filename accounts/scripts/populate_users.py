import os
import django
import random
from faker import Faker
from django.contrib.auth.models import Group
from django.db import IntegrityError
from datetime import date
from django.utils import timezone

# يجب أن تحدد مكان إعدادات جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

# استيراد النماذج
from accounts.models import User
from teachers.models import Teacher, TeacherAvailability
from students.models import Student
from admins.models import Admin
from academic.models import AcademicYear, DayOfWeek
from classes.models import Class, Section

def run():
    """
    Populates the database with fake data for User, Admin, Teacher, and Student models.
    """
    print("بدء عملية ملء بيانات المستخدمين (مدراء، معلمين، طلاب)...")

    # حذف البيانات القديمة لمنع التكرار.
    # يتم حذف المستخدمين التابعين للنماذج فقط، لتجنب حذف المستخدمين الآخرين
    Admin.objects.all().delete()
    Teacher.objects.all().delete()
    Student.objects.all().delete()
    User.objects.filter(is_superuser=False).delete() # حذف المستخدمين العاديين فقط
    print("تم حذف البيانات السابقة بنجاح.")

    # إعداد Faker باللغة العربية
    fake = Faker('ar_SA')
    
    # -------------------------------------------------------------------------
    # 1. التحقق من وجود المجموعات وإنشاؤها إن لم توجد
    # -------------------------------------------------------------------------
    print("\nجاري التحقق من وجود المجموعات (Groups)...")
    Group.objects.get_or_create(name='Student')
    Group.objects.get_or_create(name='Teacher')
    Group.objects.get_or_create(name='Manager')
    print("تم التأكد من وجود المجموعات المطلوبة.")

    # -------------------------------------------------------------------------
    # 2. التحقق من وجود الاعتماديات الأساسية (الصفوف، الشعب، العام الدراسي)
    # -------------------------------------------------------------------------
    academic_year = AcademicYear.objects.filter(is_current=True).first()
    if not academic_year:
        print("خطأ: يجب أن يكون هناك عام دراسي حالي ومحدد في قاعدة البيانات.")
        return
        
    classes = list(Class.objects.all())
    sections = list(Section.objects.all())
    day_of_weeks = list(DayOfWeek.objects.all())

    if not all([classes, sections, day_of_weeks]):
        print("خطأ: لا توجد بيانات كافية لملء الحقول المرتبطة.")
        print("الرجاء التأكد من تشغيل سكريبتات ملء بيانات الصفوف والشعب والسنوات الدراسية والأيام أولاً.")
        return

    # -------------------------------------------------------------------------
    # 3. إنشاء بيانات المستخدمين (المدراء، المعلمين، الطلاب)
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء المستخدمين...")
    admin_users_data = []
    teacher_users_data = []
    student_users_data = []
    
    # إنشاء بيانات للمدراء
    for i in range(2):
        phone = f"0911{random.randint(100000, 999999)}"
        admin_users_data.append({
            'phone_number': phone,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'department': fake.job()
        })
        
    # إنشاء بيانات للمعلمين
    for i in range(15):
        phone = f"0933{random.randint(100000, 999999)}"
        teacher_users_data.append({
            'phone_number': phone,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'specialization': fake.job()
        })

    # إنشاء بيانات للطلاب
    for i in range(50):
        phone = f"0999{random.randint(100000, 999999)}"
        student_users_data.append({
            'phone_number': phone,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'father_name': fake.first_name_male(),
            'gender': random.choice(['Male', 'Female']),
            'address': fake.address(),
            'parent_phone': f"0998{random.randint(100000, 999999)}",
            'student_class': random.choice(classes),
            'section': random.choice(sections),
            'date_of_birth': fake.date_of_birth(minimum_age=6, maximum_age=18)
        })

    # -------------------------------------------------------------------------
    # 4. حفظ البيانات في قاعدة البيانات
    # -------------------------------------------------------------------------
    print("\nجاري حفظ بيانات المدراء...")
    for data in admin_users_data:
        try:
            user = User.objects.create_admin_user(
                phone_number=data['phone_number'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password="password123",
            )
            Admin.objects.create(
                user=user,
                department=data['department']
            )
        except IntegrityError:
            print(f"تحذير: المستخدم {data['phone_number']} موجود بالفعل.")
    print(f"تم إنشاء {len(admin_users_data)} مسؤول بنجاح.")


    print("\nجاري حفظ بيانات المعلمين...")
    for data in teacher_users_data:
        try:
            user = User.objects.create_teacher_user(
                phone_number=data['phone_number'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password="password123",
            )
            teacher = Teacher.objects.create(
                user=user,
                address=fake.address(),
                specialization=data['specialization']
            )
            # إضافة توافر عشوائي للمعلم
            if day_of_weeks:
                random_days = random.sample(day_of_weeks, k=min(3, len(day_of_weeks)))
                for day in random_days:
                    TeacherAvailability.objects.create(teacher=teacher, day_of_week=day)
        except IntegrityError:
            print(f"تحذير: المستخدم {data['phone_number']} موجود بالفعل.")
    print(f"تم إنشاء {len(teacher_users_data)} معلم بنجاح.")


    print("\nجاري حفظ بيانات الطلاب...")
    for data in student_users_data:
        try:
            user = User.objects.create_student_user(
                phone_number=data['phone_number'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password="password123",
            )
            # إنشاء نموذج الطالب
            Student.objects.create(
                user=user,
                father_name=data['father_name'],
                gender=data['gender'],
                address=data['address'],
                parent_phone=data['parent_phone'],
                student_class=data['student_class'],
                section=data['section'],
                date_of_birth=data['date_of_birth']
            )
        except IntegrityError:
            print(f"تحذير: المستخدم {data['phone_number']} موجود بالفعل.")
    print(f"تم إنشاء {len(student_users_data)} طالب بنجاح.")

    print("\nاكتملت عملية ملء بيانات المستخدمين.")

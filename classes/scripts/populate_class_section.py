import os
import django
import random
import datetime
from faker import Faker
from django.db import IntegrityError
from datetime import datetime, date, timedelta
from django.utils import timezone

# يجب أن تحدد مكان إعدادات جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolo.settings')
django.setup()

# استيراد النماذج
from ..models import Class, Section
from academic.models import AcademicYear
from django.utils import timezone

def run():
    """
    Populates the database with fake data for Class and Section models.
    """
    print("بدء عملية ملء بيانات الصفوف والشعب...")

    # حذف البيانات القديمة لمنع التكرار
    Section.objects.all().delete()
    Class.objects.all().delete()
    print("تم حذف البيانات السابقة بنجاح.")

    # إعداد Faker باللغة العربية
    fake = Faker('ar_SA')
    
    # -------------------------------------------------------------------------
    # 1. التحقق من وجود بيانات AcademicYear (الاعتمادية)
    # -------------------------------------------------------------------------
    academic_years = list(AcademicYear.objects.all())
    if not academic_years:
        print("خطأ: لا توجد سنوات دراسية في قاعدة البيانات.")
        print("الرجاء تشغيل سكريبت ملء بيانات السنوات الدراسية أولاً.")
        return
    
    # -------------------------------------------------------------------------
    # 2. إنشاء بيانات نموذج Class (الصفوف)
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء الصفوف الدراسية...")
    class_names = [
        "الصف الأول", "الصف الثاني", "الصف الثالث", "الصف الرابع", "الصف الخامس",
        "الصف السادس"
    ]
    
    classes_to_create = []
    for name in class_names:
        classes_to_create.append(
            Class(name=name, description=fake.sentence(nb_words=10))
        )
    
    Class.objects.bulk_create(classes_to_create)
    print(f"تم إنشاء {len(classes_to_create)} صف دراسي بنجاح.")
    
    # ربط الصفوف بترتيب تسلسلي
    created_classes = list(Class.objects.order_by('name'))
    for i, current_class in enumerate(created_classes):
        if i < len(created_classes) - 1:
            current_class.next_class = created_classes[i + 1]
    
    Class.objects.bulk_update(created_classes, ['next_class'])
    print("تم ربط الصفوف بنجاح.")

    # -------------------------------------------------------------------------
    # 3. إنشاء بيانات نموذج Section (الشعب)
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء الشعب الدراسية...")
    
    STREAM_TYPE_CHOICES = ['General', 'Scientific', 'Literary']
    
    sections_to_create = []
    for year in academic_years:
        for class_obj in created_classes:
            # لكل صف دراسي، سننشئ 4 شعب (أ، ب، ج، د)
            for i in range(4):
                section_name = f"شعبة {chr(0x627 + i)}" # 'أ', 'ب', 'ج', 'د'
                
                is_active = random.choice([True, False])
                # استخدام timezone.now() بدلاً من datetime.datetime.now()
                activation_date = timezone.now()
                deactivation_date = activation_date + timedelta(days=random.randint(90, 180))

                sections_to_create.append(
                    Section(
                        name=section_name,
                        stream_type='General',
                        academic_year=year,
                        class_obj=class_obj,
                        capacity=random.randint(20, 40),
                        is_active=is_active,
                        activation_date=activation_date,
                        deactivation_date=deactivation_date
                    )
                )

    Section.objects.bulk_create(sections_to_create)
    print(f"تم إنشاء {len(sections_to_create)} شعبة بنجاح.")
    
    print("\nاكتملت عملية ملء بيانات الصفوف والشعب.")

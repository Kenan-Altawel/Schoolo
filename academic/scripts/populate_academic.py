import os
import django
from faker import Faker
import datetime
import random

# يجب أن تحدد مكان إعدادات جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolo.settings')
django.setup()

# استيراد النماذج بعد إعداد جانغو
from ..models import AcademicYear, AcademicTerm, TimeSlot

def run():
    print("بدء عملية ملء البيانات الوهمية...")

    # حذف البيانات القديمة لمنع التكرار
    AcademicTerm.objects.all().delete()
    AcademicYear.objects.all().delete()
    TimeSlot.objects.all().delete()
    print("تم حذف البيانات السابقة بنجاح.")

    # إعداد Faker باللغة العربية
    fake = Faker('ar_SA')
    
    # -------------------------------------------------------------------------
    # 1. إنشاء بيانات لنموذج AcademicYear
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء السنوات الدراسية...")
    NUM_YEARS = 5
    years_to_create = []
    
    current_year = datetime.date.today().year
    
    for i in range(NUM_YEARS):
        # إنشاء سنوات دراسية تبدأ من العام الحالي وتتراجع
        start_date = datetime.date(current_year - i, 9, 1) # يبدأ العام الدراسي في سبتمبر
        end_date = datetime.date(current_year - i + 1, 6, 30) # وينتهي في يونيو من العام التالي
        is_current = (i == 0) # العام الأخير هو العام الحالي
        
        year = AcademicYear(
            name=f"العام الدراسي {start_date.year}/{end_date.year}",
            start_date=start_date,
            end_date=end_date,
            is_current=is_current
        )
        years_to_create.append(year)
    
    AcademicYear.objects.bulk_create(years_to_create)
    print(f"تم إنشاء {NUM_YEARS} عام دراسي بنجاح.")

    # -------------------------------------------------------------------------
    # 2. إنشاء بيانات لنموذج AcademicTerm (يعتمد على AcademicYear)
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء الفصول الدراسية...")
    created_years = list(AcademicYear.objects.all())
    terms_to_create = []
    
    for year in created_years:
        # إنشاء فصلين دراسيين لكل عام
        term1_start = year.start_date
        term1_end = term1_start + datetime.timedelta(days=120)
        
        term2_start = term1_end + datetime.timedelta(days=14) # فترة استراحة
        term2_end = year.end_date
        
        is_current_term = (year.is_current and year.name.endswith('2025/2026') ) # يمكنك تعديل هذا الشرط
        
        term1 = AcademicTerm(
            academic_year=year,
            name="الفصل الأول",
            start_date=term1_start,
            end_date=term1_end,
            is_current=is_current_term
        )
        term2 = AcademicTerm(
            academic_year=year,
            name="الفصل الثاني",
            start_date=term2_start,
            end_date=term2_end,
            is_current=False
        )
        terms_to_create.append(term1)
        terms_to_create.append(term2)
        
    AcademicTerm.objects.bulk_create(terms_to_create)
    print(f"تم إنشاء {len(terms_to_create)} فصل دراسي بنجاح.")

    # -------------------------------------------------------------------------
    # 3. إنشاء بيانات لنموذج TimeSlot
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء الفترات الزمنية للحصص...")
    time_slots_to_create = []
    num_slots = 6
    
    start_hour = 8
    start_minute = 0
    slot_duration = 45 # بالدقائق
    break_duration = 15
    
    for i in range(1, num_slots + 1):
        is_break = (i == 4) # الحصة الرابعة ستكون استراحة
        
        start_time = datetime.time(start_hour, start_minute)
        
        if is_break:
            end_time = (datetime.datetime.combine(datetime.date.today(), start_time) + datetime.timedelta(minutes=break_duration)).time()
            name = f"الاستراحة {i-3}"
        else:
            end_time = (datetime.datetime.combine(datetime.date.today(), start_time) + datetime.timedelta(minutes=slot_duration)).time()
            name = f"الحصة {i}"
        
        time_slot = TimeSlot(
            slot_number=i,
            name=name,
            start_time=start_time,
            end_time=end_time,
            is_break=is_break
        )
        time_slots_to_create.append(time_slot)
        
        # تحديد وقت بداية الحصة التالية
        start_hour = end_time.hour
        start_minute = end_time.minute
    
    TimeSlot.objects.bulk_create(time_slots_to_create)
    print(f"تم إنشاء {num_slots} فترة زمنية بنجاح.")

    print("\nاكتملت عملية ملء قاعدة البيانات.")
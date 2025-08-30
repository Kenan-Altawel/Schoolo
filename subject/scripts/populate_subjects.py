import os
import django
import random
from faker import Faker
from django.db import IntegrityError
from django.utils import timezone

# يجب أن تحدد مكان إعدادات جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolo.settings')
django.setup()

# استيراد النماذج
from subject.models import SubjectIcon, Subject, TeacherSubject, SectionSubjectRequirement
from academic.models import AcademicYear, AcademicTerm
from classes.models import Class, Section
from teachers.models import Teacher


def run():
    """
    Populates the database with fake data for Subject and related models.
    """
    print("بدء عملية ملء بيانات المواد الدراسية...")

    # حذف البيانات القديمة لمنع التكرار
    SectionSubjectRequirement.objects.all().delete()
    TeacherSubject.objects.all().delete()
    Subject.objects.all().delete()
    SubjectIcon.objects.all().delete()
    print("تم حذف البيانات السابقة بنجاح.")

    # إعداد Faker باللغة العربية
    fake = Faker('ar_SA')

    # -------------------------------------------------------------------------
    # 1. التحقق من وجود البيانات الأساسية (الاعتماديات)
    # -------------------------------------------------------------------------
    academic_years = list(AcademicYear.objects.all())
    academic_terms = list(AcademicTerm.objects.all())
    classes = list(Class.objects.all())
    sections = list(Section.objects.all())
    teachers = list(Teacher.objects.all())

    if not all([academic_years, academic_terms, classes, sections, teachers]):
        print("خطأ: لا توجد بيانات كافية في قاعدة البيانات.")
        print("الرجاء التأكد من تشغيل سكريبتات ملء بيانات AcademicYear, AcademicTerm, Class, Section, و Teachers أولاً.")
        return

    # -------------------------------------------------------------------------
    # 2. إنشاء أيقونات المواد الدراسية
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء أيقونات المواد الدراسية...")
    icon_names = ["رياضيات", "فيزياء", "كيمياء", "أحياء", "لغة عربية", "لغة إنجليزية", "تاريخ", "جغرافيا"]
    icons_to_create = [SubjectIcon(name=name) for name in icon_names]
    SubjectIcon.objects.bulk_create(icons_to_create)
    created_icons = list(SubjectIcon.objects.all())
    print(f"تم إنشاء {len(created_icons)} أيقونة بنجاح.")

    # -------------------------------------------------------------------------
    # 3. إنشاء المواد الدراسية
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء المواد الدراسية...")
    subject_names = [
        "رياضيات متقدمة", "فيزياء حديثة", "كيمياء عضوية", "أحياء عامة", "لغة عربية",
        "لغة إنجليزية", "تاريخ إسلامي", "جغرافيا طبيعية", "علوم", "فنون", "تربية إسلامية"
    ]
    STREAM_TYPE_CHOICES = ['General', 'Scientific', 'Literary']
    
    subjects_to_create = []

    # إنشاء مواد عامة لكل صف
    for class_obj in classes:
        for term in academic_terms:
            for year in academic_years:
                subject_name = random.choice(subject_names)
                subjects_to_create.append(
                    Subject(
                        class_obj=class_obj,
                        stream_type='General',
                        name=f"{subject_name} - {class_obj.name}",
                        is_active=True,
                        icon=random.choice(created_icons),
                        default_weekly_lessons=random.randint(2, 6),
                        academic_year=year,
                        academic_term=term
                    )
                )

    # إنشاء مواد محددة لشعب معينة
    for section in sections:
        for term in academic_terms:
            for year in academic_years:
                subject_name = random.choice(subject_names)
                subjects_to_create.append(
                    Subject(
                        section=section,
                        name=f"{subject_name} - {section.name}",
                        is_active=True,
                        icon=random.choice(created_icons),
                        default_weekly_lessons=random.randint(2, 6),
                        academic_year=year,
                        academic_term=term
                    )
                )

    Subject.objects.bulk_create(subjects_to_create)
    created_subjects = list(Subject.objects.all())
    print(f"تم إنشاء {len(created_subjects)} مادة دراسية بنجاح.")

    # -------------------------------------------------------------------------
    # 4. إنشاء روابط مواد المعلمين
    # -------------------------------------------------------------------------
    print("\nجاري ربط المواد بالمعلمين...")
    teacher_subjects_to_create = []
    for teacher in teachers:
        # ربط كل معلم بـ 3 مواد عشوائية
        random_subjects = random.sample(created_subjects, k=min(3, len(created_subjects)))
        for subject in random_subjects:
            teacher_subjects_to_create.append(
                TeacherSubject(
                    teacher=teacher,
                    subject=subject,
                    weekly_hours=random.randint(2, 10)
                )
            )

    try:
        TeacherSubject.objects.bulk_create(teacher_subjects_to_create)
        print(f"تم ربط {len(teacher_subjects_to_create)} مادة بمعلميها بنجاح.")
    except IntegrityError:
        print("تحذير: فشل في إنشاء بعض روابط المعلمين والمواد بسبب التكرار.")
    
    # -------------------------------------------------------------------------
    # 5. إنشاء متطلبات الحصص لكل شعبة
    # -------------------------------------------------------------------------
    print("\nجاري إنشاء متطلبات الحصص للشعب...")
    section_requirements_to_create = []
    for section in sections:
        # اختيار 5 مواد بشكل عشوائي لكل شعبة
        random_subjects = random.sample(created_subjects, k=min(5, len(created_subjects)))
        for subject in random_subjects:
            section_requirements_to_create.append(
                SectionSubjectRequirement(
                    section=section,
                    subject=subject,
                    weekly_lessons_required=random.randint(2, 6)
                )
            )

    try:
        SectionSubjectRequirement.objects.bulk_create(section_requirements_to_create)
        print(f"تم إنشاء {len(section_requirements_to_create)} متطلب حصص للشعب بنجاح.")
    except IntegrityError:
        print("تحذير: فشل في إنشاء بعض متطلبات الحصص بسبب التكرار.")

    print("\nاكتملت عملية ملء بيانات المواد الدراسية.")

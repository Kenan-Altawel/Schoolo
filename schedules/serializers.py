from rest_framework import serializers
from academic.models import AcademicYear, AcademicTerm, DayOfWeek, TimeSlot
from classes.models import Class, Section
from subject.models import Subject, SectionSubjectRequirement, TeacherSubject
from teachers.models import Teacher, TeacherAvailability
from schedules.models import ClassSchedule, ProposedClassSchedule # تأكد من استيراد هذه الموديلات من تطبيق schedules الخاص بك


# Serializer للمادة الدراسية مع حساب الحصص المضافة والمطلوبة
class SubjectWithLessonCountSerializer(serializers.ModelSerializer):
    added_lessons = serializers.SerializerMethodField()
    total_lessons_required = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'description', 'is_active',
            'default_weekly_lessons', 'added_lessons', 'total_lessons_required'
        ]

    def get_added_lessons(self, obj):
        # يحسب عدد الحصص المضافة لهذه المادة في سياق الصف والشعبة
        school_class_id = self.context.get('class_id') # تم تغيير الاسم ليتناسب مع Class Model
        section_id = self.context.get('section_id')

        if school_class_id and section_id:
            count = ClassSchedule.objects.filter(
                section_id=section_id,
                subject=obj
            ).count()
            return count
        return 0

    def get_total_lessons_required(self, obj):
        # يجلب عدد الحصص المطلوبة من SectionSubjectRequirement
        section_id = self.context.get('section_id')
        if section_id:
            try:
                requirement = SectionSubjectRequirement.objects.get(
                    section_id=section_id,
                    subject=obj
                )
                return requirement.weekly_lessons_required
            except SectionSubjectRequirement.DoesNotExist:
                # إذا لم يتم تحديد متطلب خاص للشعبة، نعود للقيمة الافتراضية في المادة
                return obj.default_weekly_lessons
        return obj.default_weekly_lessons 


# Serializer لإنشاء وتعديل وعرض ClassSchedule
class ClassScheduleSerializer(serializers.ModelSerializer):
    # استخدام SlugRelatedField لعرض الأسماء بدلاً من الـ IDs
    subject_name = serializers.SlugRelatedField(source='subject', slug_field='name', read_only=True)
    section_name = serializers.SlugRelatedField(source='section', slug_field='name', read_only=True)
    teacher_name = serializers.SerializerMethodField()    
    academic_year_name = serializers.SlugRelatedField(source='academic_year', slug_field='name', read_only=True)
    academic_term_name = serializers.SlugRelatedField(source='academic_term', slug_field='name', read_only=True)
    day_of_week_display = serializers.SlugRelatedField(
        source='day_of_week',
        slug_field='name_ar',
        read_only=True
    )
    time_slot_display = serializers.SlugRelatedField(
        source='time_slot',
        slug_field='name',
        read_only=True
    )
    start_slot = serializers.SlugRelatedField(
        source='time_slot',
        slug_field='start_time',
        read_only=True
    )
    end_slot = serializers.SlugRelatedField(
        source='time_slot',
        slug_field='end_time',
        read_only=True
    )
    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name()
        return None
    
    class Meta:
        model = ClassSchedule
        fields = [
            'id', 'subject', 'subject_name', 'section', 'section_name',
            'teacher', 'teacher_name', 'academic_year', 'academic_year_name',
            'academic_term', 'academic_term_name', 'day_of_week', 'day_of_week_display','time_slot', 'time_slot_display','start_slot','end_slot'
        ]
        read_only_fields = [
            'subject_name', 'section_name', 'teacher_name',
            'academic_year_name', 'academic_term_name', 'day_of_week_display','start_slot','end_slot'
        ]

    def validate(self, data):
        # التحقق من أن المعلم يدرّس المادة المختارة
        teacher = data.get('teacher')
        subject = data.get('subject')
        if not TeacherSubject.objects.filter(teacher=teacher, subject=subject).exists():
            raise serializers.ValidationError("هذا المعلم لا يدرّس هذه المادة.")
        
        # --- إضافة منطق التحقق من التضارب هنا ---
        section = data.get('section')
        day_of_week = data.get('day_of_week')
        time_slot = data.get('time_slot')        
        # 1. التحقق من تضارب الشعبة
        if ClassSchedule.objects.filter(section=section, day_of_week=day_of_week,time_slot=time_slot).exists():
            raise serializers.ValidationError("هذه الشعبة لديها حصة في نفس الوقت واليوم.")
            
        # 2. التحقق من تضارب المعلم
        if ClassSchedule.objects.filter(teacher=teacher, day_of_week=day_of_week, time_slot=time_slot).exists():
            raise serializers.ValidationError("هذا المعلم لديه حصة في نفس الوقت واليوم.")

        return data


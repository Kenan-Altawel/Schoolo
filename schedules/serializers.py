from rest_framework import serializers
from academic.models import AcademicYear, AcademicTerm, DayOfWeek, TimeSlot
from classes.models import Class, Section
from subject.models import Subject, SectionSubjectRequirement, TeacherSubject
from teachers.models import Teacher, TeacherAvailability
from schedules.models import ClassSchedule, ProposedClassSchedule # تأكد من استيراد هذه الموديلات من تطبيق schedules الخاص بك
from accounts.models import User # لاستخدام معلومات المستخدم للمعلم

# Serializer للمستخدم لعرض الاسم الكامل للمعلم
class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name()

# Serializer لموديل DayOfWeek إذا أردت استخدامه كـ ForeignKey
class DayOfWeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOfWeek
        fields = ['id', 'name_ar', 'is_school_day']

# Serializer لموديل TimeSlot إذا أردت استخدامه كـ ForeignKey
class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'slot_number', 'start_time', 'end_time', 'is_break']

# Serializer للمعلم، يتضمن أيامه المفضلة
class TeacherSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    preferred_days = serializers.SerializerMethodField()
    teaches_subjects = serializers.SerializerMethodField() # لعرض المواد التي يدرسها

    class Meta:
        model = Teacher
        fields = ['user', 'address', 'specialization', 'preferred_days', 'teaches_subjects']

    def get_preferred_days(self, obj):
        # جلب الأيام المفضلة من TeacherAvailability
        availability = obj.availability.all().order_by('day_of_week')
        return [item.get_day_of_week_display() for item in availability]

    def get_teaches_subjects(self, obj):
        # جلب المواد التي يدرسها المعلم من TeacherSubject
        teacher_subjects = obj.teaching_subjects.all()
        return [ts.subject.name for ts in teacher_subjects]


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
            # يجب التأكد أن ClassSchedule يربط بـ Class و Section بشكل صحيح
            # ClassSchedule يربط بـ Section فقط، و Section يربط بـ Class
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
        return obj.default_weekly_lessons # fallback


# Serializer لإنشاء وتعديل وعرض ClassSchedule
class ClassScheduleSerializer(serializers.ModelSerializer):
    # استخدام SlugRelatedField لعرض الأسماء بدلاً من الـ IDs
    subject_name = serializers.SlugRelatedField(source='subject', slug_field='name', read_only=True)
    section_name = serializers.SlugRelatedField(source='section', slug_field='name', read_only=True)
    teacher_name = serializers.SlugRelatedField(source='teacher.user', slug_field='get_full_name', read_only=True)
    academic_year_name = serializers.SlugRelatedField(source='academic_year', slug_field='name', read_only=True)
    academic_term_name = serializers.SlugRelatedField(source='academic_term', slug_field='name', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)


    class Meta:
        model = ClassSchedule
        fields = [
            'id', 'subject', 'subject_name', 'section', 'section_name',
            'teacher', 'teacher_name', 'academic_year', 'academic_year_name',
            'academic_term', 'academic_term_name', 'day_of_week', 'day_of_week_display', 'period'
        ]
        read_only_fields = [
            'subject_name', 'section_name', 'teacher_name',
            'academic_year_name', 'academic_term_name', 'day_of_week_display'
        ]

    def validate(self, data):
        # التحقق من أن المعلم يدرّس المادة المختارة
        teacher = data.get('teacher')
        subject = data.get('subject')
        if teacher and subject:
            if not TeacherSubject.objects.filter(teacher=teacher, subject=subject).exists():
                raise serializers.ValidationError("هذا المعلم لا يدرّس هذه المادة.")

        # يمكن إضافة تحققات إضافية هنا إذا لزم الأمر قبل حفظ الكائن
        # (مثلاً، التأكد من أن العام والفصل الدراسيين نشطين)
        return data


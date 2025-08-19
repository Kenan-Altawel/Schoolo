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
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id', 'class_obj', 'section', 'stream_type', 'name',
            'description', 'is_active', 'pdf_file', 'icon', 'icon_url',
            'default_weekly_lessons', 'academic_year', 'academic_term',
            'added_lessons', 'total_lessons_required'
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

    def get_icon_url(self, obj):
        """
        هذه الدالة تقوم بإرجاع URL الأيقونة المرتبطة بالمادة.
        """
        if obj.icon and obj.icon.icon_file:
            # استخدام .url للحصول على المسار الكامل للملف
            return self.context['request'].build_absolute_uri(obj.icon.icon_file.url)
        return None


class SubjectRemainingLessonsSerializer(serializers.ModelSerializer):
    """Serializer مبسّط لعرض كل مادة وعدد الحصص المتبقية لها في شعبة معينة للفصل/العام الحاليين."""
    added_lessons = serializers.SerializerMethodField()
    total_lessons_required = serializers.SerializerMethodField()
    remaining_lessons = serializers.SerializerMethodField()
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'icon_url',
            'added_lessons', 'total_lessons_required', 'remaining_lessons'
        ]

    def _get_current_year_and_term(self):
        try:
            current_year = AcademicYear.objects.get(is_current=True)
            current_term = AcademicTerm.objects.get(is_current=True, academic_year=current_year)
            return current_year, current_term
        except (AcademicYear.DoesNotExist, AcademicTerm.DoesNotExist):
            return None, None

    def _get_section(self):
        section_id = self.context.get('section_id')
        if not section_id:
            return None
        try:
            return Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return None

    def get_icon_url(self, obj):
        if obj.icon and obj.icon.icon_file and 'request' in self.context:
            return self.context['request'].build_absolute_uri(obj.icon.icon_file.url)
        return None

    def get_total_lessons_required(self, obj):
        section = self._get_section()
        if not section:
            return obj.default_weekly_lessons
        try:
            req = SectionSubjectRequirement.objects.get(section=section, subject=obj)
            return req.weekly_lessons_required
        except SectionSubjectRequirement.DoesNotExist:
            return obj.default_weekly_lessons

    def get_added_lessons(self, obj):
        section = self._get_section()
        if not section:
            return 0
        current_year, current_term = self._get_current_year_and_term()
        filters = {'section': section, 'subject': obj}
        if current_year and current_term:
            filters.update({'academic_year': current_year, 'academic_term': current_term})
        return ClassSchedule.objects.filter(**filters).count()

    def get_remaining_lessons(self, obj):
        required = self.get_total_lessons_required(obj)
        added = self.get_added_lessons(obj)
        remaining = required - added
        return remaining if remaining > 0 else 0


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
            'academic_term', 'academic_term_name', 'day_of_week', 'day_of_week_display',
            'time_slot', 'time_slot_display', 'start_slot', 'end_slot'
        ]
        read_only_fields = [
            'subject_name', 'section_name', 'teacher_name',
            'academic_year_name', 'academic_term_name', 'day_of_week_display',
            'start_slot', 'end_slot'
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
        if ClassSchedule.objects.filter(section=section, day_of_week=day_of_week, time_slot=time_slot).exists():
            raise serializers.ValidationError("هذه الشعبة لديها حصة في نفس الوقت واليوم.")

        # 2. التحقق من تضارب المعلم
        if ClassSchedule.objects.filter(teacher=teacher, day_of_week=day_of_week, time_slot=time_slot).exists():
            raise serializers.ValidationError("هذا المعلم لديه حصة في نفس الوقت واليوم.")

        return data


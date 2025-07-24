# subject/serializers.py
from rest_framework import serializers
from .models import Subject, SectionSubjectRequirement
from classes.models import Class, Section
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class SectionSubjectRequirementSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='section.name', read_only=True)
    class_name = serializers.CharField(source='section.class_obj.name', read_only=True)

    class Meta:
        model = SectionSubjectRequirement
        fields = ['id', 'section', 'subject', 'weekly_lessons_required', 'section_name', 'class_name']
        read_only_fields = ['subject']


class SubjectSerializer(serializers.ModelSerializer):
    class_obj = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all(), allow_null=True, required=False,
        label=_("الفصل الدراسي المستهدف")
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), allow_null=True, required=False,
        label=_("الشعبة المستهدفة")
    )

    class_obj_name = serializers.CharField(source='class_obj.name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    stream_type_display = serializers.CharField(source='get_stream_type_display', read_only=True)

    # pdf_file = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'description', 'stream_type', 'is_active',
            'pdf_file',
            'class_obj', 'section',
            'class_obj_name', 'section_name', 'stream_type_display',
            'default_weekly_lessons',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')

    # def get_pdf_file(self, obj):
    #     if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
    #         return obj.pdf_file.url
    #     return None

    def validate(self, data):
        class_obj = data.get('class_obj')
        section_obj = data.get('section')
        stream_type = data.get('stream_type')

        is_linked_to_class = class_obj is not None
        is_linked_to_section = section_obj is not None

        # **تعديل:** تعريف "المادة العامة" يشمل stream_type=None أو stream_type='General'
        is_subject_general = (stream_type is None) or (stream_type == 'General')

        # 1. التحقق الأساسي: المادة يجب أن ترتبط بصف دراسي (class_obj) أو شعبة محددة (section) على الأقل.
        if not is_linked_to_class and not is_linked_to_section:
            raise serializers.ValidationError(
                _("المادة يجب أن ترتبط بصف دراسي (class_obj) أو شعبة محددة (section).")
            )

        # 2. التحقق إذا تم تحديد شعبة (section_obj):
        if is_linked_to_section:
            # أ. يجب تحديد الصف (class_obj) الذي تنتمي إليه الشعبة.
            if not is_linked_to_class:
                raise serializers.ValidationError({
                    "class_obj": _("عند تحديد شعبة، يجب تحديد الصف الدراسي المرتبطة به.")
                })

            # ب. التحقق من أن الشعبة تنتمي فعلاً إلى الصف المحدد.
            if section_obj.class_obj != class_obj:
                raise serializers.ValidationError({
                    "section": _("الشعبة المحددة لا تنتمي للفصل الدراسي المدخل.")
                })

            # ج. التحقق من توافق stream_type للمادة مع stream_type للشعبة.
            # هذا التحقق يتم فقط إذا كانت المادة "ليست عامة" (أي Scientific أو Literary)
            if not is_subject_general:  # إذا كانت المادة ليست عامة (أي Scientific أو Literary)
                # إذا كانت الشعبة نفسها لها stream_type محدد (ليست عامة)
                if section_obj.stream_type:
                    # يجب أن يتطابق stream_type الخاص بالمادة مع stream_type الخاص بالشعبة
                    if section_obj.stream_type != stream_type:
                        raise serializers.ValidationError({
                            "stream_type": _("نوع مسار المادة لا يتوافق مع نوع مسار الشعبة المحددة.")
                        })
                # أما إذا كانت الشعبة ليس لديها stream_type محدد (شعبة عامة: section_obj.stream_type is None)
                # والسيريالايزر تلقى stream_type للمادة (Scientific/Literary)، فهذا مسموح به.
                # (مادة علمية تُدرّس في شعبة عامة).

        # 3. **التحقق الجديد/المعدّل:** منع ربط مادة "عامة" (stream_type=None أو 'General') بشعبة محددة.
        # إذا كانت المادة عامة (حسب تعريف is_subject_general الجديد)
        # و في نفس الوقت تم تحديد شعبة محددة للمادة (section_obj له قيمة)
        if is_subject_general and is_linked_to_section:  # **تم تعديل الشرط هنا**
            raise serializers.ValidationError({
                "non_field_errors": _(
                    "لا يمكن ربط مادة عامة (بدون مسار محدد أو بمسار 'عام') بشعبة واحدة محددة. المادة العامة تُربط بجميع شعب الصف تلقائياً.")
            })

        # 4. التحقق من صحة قيمة stream_type إذا تم تحديدها:
        # هذا الشرط يضمن أن القيمة المدخلة لـ stream_type (إذا وُجدت) هي قيمة صالحة من CHOICES
        # (بما في ذلك 'General' الآن).
        # ملاحظة: هذا التحقق لا يسبب خطأ إذا كانت القيمة None، لأن is_stream_specified تكون False في هذه الحالة.
        if stream_type is not None and stream_type not in [choice[0] for choice in Subject.STREAM_TYPE_CHOICES]:
            raise serializers.ValidationError(_("نوع المسار المدخل غير صالح."))

        # 5. التحقق المنطقي: إذا تم تحديد stream_type للمادة ولكن لم يتم تحديد الصف، هذا خطأ.
        # (لأن stream_type للمادة يجب أن يرتبط بسياق صف دراسي).
        # هذا الشرط يحتاج لتعديل طفيف ليأخذ في الاعتبار أن 'General' هو أيضاً stream_type محدد الآن.
        # لذا، "stream_type محدد" تعني أي قيمة غير None.
        if stream_type is not None and not is_linked_to_class:  # **تم تعديل الشرط هنا**
            raise serializers.ValidationError(
                _("نوع المسار (stream_type) يجب أن يُحدد فقط عند ربط المادة بصف دراسي (class_obj).")
            )

        # 6. التحقق من default_weekly_lessons
        default_weekly_lessons = data.get('default_weekly_lessons')
        if default_weekly_lessons is not None and default_weekly_lessons <= 0:
            raise serializers.ValidationError(_("عدد الحصص الأسبوعية الافتراضي يجب أن يكون رقماً صحيحاً وموجباً."))

        return data
    
from .models import Subject, TeacherSubject # تأكد من استيراد TeacherSubject و Subject

class TeacherSubjectAssignmentSerializer(serializers.Serializer):
    """
    سيريالايزر يستخدم لتلقي بيانات ربط المادة بالمعلم (لعمليات الإنشاء/التحديث)
    """
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        label=_("معرف المادة"),
        help_text=_("المعرف الفريد للمادة المراد ربطها بالمعلم.")
    )
    weekly_hours = serializers.IntegerField(
        min_value=1,
        max_value=30, 
        label=_("الساعات الأسبوعية"),
        help_text=_("عدد الحصص الأسبوعية التي يدرسها المعلم لهذه المادة.")
    )

    def validate_subject_id(self, value):
        if not Subject.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(_("المادة المحددة غير موجودة."))
        return value

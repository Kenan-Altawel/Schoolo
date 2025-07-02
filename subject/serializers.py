# subject/serializers.py
from rest_framework import serializers
from .models import Subject, SectionSubjectRequirement
from classes.models import Class, Section
from django.utils.translation import gettext_lazy as _
from django.conf import settings # لاستخدام MEDIA_URL إذا لزم الأمر



class SubjectSerializer(serializers.ModelSerializer):
    class_obj = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all(), allow_null=True, required=False,
        label=_("الفصل الدراسي")
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), allow_null=True, required=False,
        label=_("الشعبة")
    )

    class_obj_name = serializers.CharField(source='class_obj.name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    stream_type_display = serializers.CharField(source='get_stream_type_display', read_only=True)

    pdf_file = serializers.SerializerMethodField()

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

    def get_pdf_file(self, obj):
        if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
            return obj.pdf_file.url
        return None

    def validate(self, data):
        class_obj = data.get('class_obj')
        section_obj = data.get('section')
        stream_type = data.get('stream_type')

        is_linked_to_class = class_obj is not None
        is_linked_to_section = section_obj is not None
        is_stream_specified = stream_type is not None

        # 1. المادة يجب أن ترتبط بصف دراسي (class_obj) أو شعبة محددة (section) على الأقل.
        if not is_linked_to_class and not is_linked_to_section:
            raise serializers.ValidationError(
                _("المادة يجب أن ترتبط بصف دراسي (class_obj) أو شعبة محددة (section).")
            )

        # 2. إذا تم تحديد شعبة (section_obj):
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

            # ج. التحقق من توافق stream_type للمادة مع stream_type للشعبة (إذا كانت المادة لديها stream_type).
            # هذه هي النقطة التي تسمح بتحديد stream_type للمادة حتى لو كانت مربوطة بشعبة.
            if is_stream_specified:
                # إذا كانت الشعبة نفسها لها stream_type محدد (ليست عامة)
                if section_obj.stream_type:
                    # يجب أن يتطابق stream_type الخاص بالمادة مع stream_type الخاص بالشعبة
                    if section_obj.stream_type != stream_type:
                        raise serializers.ValidationError({
                            "stream_type": _("نوع مسار المادة لا يتوافق مع نوع مسار الشعبة المحددة.")
                        })
                # أما إذا كانت الشعبة ليس لديها stream_type محدد (شعبة عامة: section_obj.stream_type is None)
                # والسيريالايزر تلقى stream_type للمادة، هذا مسموح به. (مادة علمية تُدرّس في شعبة عامة)

        # 3. إذا لم يتم تحديد شعبة (section_obj) ولكن تم تحديد الصف (class_obj):
        # هذا هو السيناريو الذي تكون فيه المادة لصف كامل (مع أو بدون مسار محدد).
        # التحقق الوحيد هنا هو أن stream_type (إن وجد) يجب أن يكون صالحاً، وهو ما يغطيه الشرط 4.

        # 4. التحقق من صحة قيمة stream_type إذا تم تحديدها:
        if is_stream_specified and stream_type not in [choice[0] for choice in Subject.STREAM_TYPE_CHOICES]:
            raise serializers.ValidationError(_("نوع المسار المدخل غير صالح."))

        # 5. إذا تم تحديد stream_type للمادة ولكن لم يتم تحديد الصف، هذا خطأ.
        # (لأن stream_type لا معنى له بدون سياق صف دراسي).
        if is_stream_specified and not is_linked_to_class:
            raise serializers.ValidationError(
                _("نوع المسار (stream_type) يجب أن يُحدد فقط عند ربط المادة بصف دراسي (class_obj).")
            )

        default_weekly_lessons = data.get('default_weekly_lessons')
        if default_weekly_lessons is not None and default_weekly_lessons <= 0:
            raise serializers.ValidationError(_("عدد الحصص الأسبوعية الافتراضي يجب أن يكون رقماً صحيحاً وموجباً."))

        return data


class SectionSubjectRequirementSerializer(serializers.ModelSerializer):
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
    )

    section_name = serializers.CharField(source='section.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    class_name = serializers.CharField(source='section.class_obj.name', read_only=True)

    class Meta:
        model = SectionSubjectRequirement
        fields = [
            'id', 'section', 'subject', 'weekly_lessons_required',
            'section_name', 'subject_name', 'class_name'
        ]
        read_only_fields = ['section_name', 'subject_name', 'class_name']
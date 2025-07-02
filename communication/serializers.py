# communication/serializers.py
from rest_framework import serializers
from .models import NewsActivity
from classes.models import Class, Section
from subject.models import Subject
from accounts.models import User # تأكد من استيراد نموذج المستخدم المخصص الخاص بك
from django.utils.translation import gettext_lazy as _
import datetime

class NewsActivitySerializer(serializers.ModelSerializer):
    # حقول للقراءة فقط لعرض اسم المستخدم الذي أنشأ الإعلان، ونوع الجمهور والنوع
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    target_audience_display = serializers.CharField(source='get_target_audience_display', read_only=True)

    # حقول SlugRelatedField للسماح بإرسال اسم الفصل/القسم/المادة بدلاً من الـ ID
    target_class = serializers.SlugRelatedField(
        queryset=Class.objects.all(),
        slug_field='name', # استخدم 'name' للبحث عن الكائن
        allow_null=True,
        required=False,
        label=_("الفصل المستهدف (بالاسم)")
    )
    target_section = serializers.SlugRelatedField(
        queryset=Section.objects.all(),
        slug_field='name', # استخدم 'name' للبحث عن الكائن
        allow_null=True,
        required=False,
        label=_("القسم المستهدف (بالاسم)")
    )
    target_subject = serializers.SlugRelatedField(
        queryset=Subject.objects.all(),
        slug_field='name', # استخدم 'name' للبحث عن الكائن
        allow_null=True,
        required=False,
        label=_("المادة المستهدفة (بالاسم)")
    )

    # حقول للقراءة فقط لعرض أسماء الفصل/القسم/المادة المرتبطة
    target_class_name = serializers.CharField(source='target_class.name', read_only=True)
    target_section_name = serializers.CharField(source='target_section.name', read_only=True)
    target_subject_name = serializers.CharField(source='target_subject.name', read_only=True)


    class Meta:
        model = NewsActivity
        fields = [
            'id', 'title', 'description', 'created_by', 'created_by_username',
            'type', 'type_display', 'target_audience', 'target_audience_display',
            'target_class', 'target_class_name',
            'target_section', 'target_section_name',
            'target_subject', 'target_subject_name',
            'activity_date', 'created_at', 'updated_at'
        ]
        # created_by و created_at و updated_at هي حقول للقراءة فقط ويتم تعيينها تلقائياً
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def validate(self, data):
        # الحصول على القيم الحالية أو القيم الجديدة من البيانات
        news_type = data.get('type', self.instance.type if self.instance else 'announcement')
        target_audience = data.get('target_audience', self.instance.target_audience if self.instance else 'all')
        activity_date = data.get('activity_date', self.instance.activity_date if self.instance else None)
        target_class = data.get('target_class', self.instance.target_class if self.instance else None)
        target_section = data.get('target_section', self.instance.target_section if self.instance else None)
        target_subject = data.get('target_subject', self.instance.target_subject if self.instance else None)


        errors = {}

        if news_type == 'activity' and not activity_date:
            errors['activity_date'] = _("يجب تحديد تاريخ النشاط إذا كان نوع الخبر 'نشاط'.")
        elif news_type == 'announcement' and activity_date:
            errors['activity_date'] = _("لا يمكن تحديد تاريخ النشاط إذا كان نوع الخبر 'إعلان'.")

        # قائمة بجميع الحقول المستهدفة المحددة (فقط الفصل، القسم، المادة)
        specific_target_fields = {
            'target_class': target_class,
            'target_section': target_section,
            'target_subject': target_subject,
        }

        # التحقق من شروط الجمهور المستهدف
        if target_audience == 'class':
            if not target_class: errors['target_class'] = _("يجب تحديد فصل دراسي مستهدف عندما يكون الجمهور 'فصل دراسي'.")
            # التأكد من أن باقي الحقول فارغة
            for field_name, field_value in specific_target_fields.items():
                if field_name != 'target_class' and field_value:
                    errors[field_name] = _("لا يمكن تحديد {field_name_display} عندما يكون الجمهور 'فصل دراسي'.").format(
                        field_name_display=self.fields[field_name].label
                    )

        elif target_audience == 'section':
            if not target_section: errors['target_section'] = _("يجب تحديد قسم مستهدف عندما يكون الجمهور 'قسم'.")
            for field_name, field_value in specific_target_fields.items():
                if field_name != 'target_section' and field_value:
                    errors[field_name] = _("لا يمكن تحديد {field_name_display} عندما يكون الجمهور 'قسم'.").format(
                        field_name_display=self.fields[field_name].label
                    )

        elif target_audience == 'subject':
            if not target_subject: errors['target_subject'] = _("يجب تحديد مادة دراسية مستهدفة عندما يكون الجمهور 'مادة دراسية'.")
            for field_name, field_value in specific_target_fields.items():
                if field_name != 'target_subject' and field_value:
                    errors[field_name] = _("لا يمكن تحديد {field_name_display} عندما يكون الجمهور 'مادة دراسية'.").format(
                        field_name_display=self.fields[field_name].label
                    )

        # شروط عامة: إذا كان الجمهور عاماً (all, teachers, students)، لا يمكن تحديد أي هدف محدد
        elif target_audience in ['all', 'teachers', 'students']:
            for field_name, field_value in specific_target_fields.items():
                if field_value: # إذا كان هناك أي حقل محدد له قيمة
                    # الحصول على اسم العرض للجمهور المستهدف (مثلاً "المعلمون" بدلاً من "teachers")
                    audience_display_name = next(
                        (choice[1] for choice in NewsActivity.TARGET_AUDIENCE_CHOICES if choice[0] == target_audience),
                        target_audience
                    )
                    errors[field_name] = _("لا يمكن تحديد هدف محدد ({field_name_display}) عندما يكون الجمهور '{audience_type}'.").format(
                        field_name_display=self.fields[field_name].label,
                        audience_type=audience_display_name
                    )

        # التحقق من أن القسم ينتمي إلى الفصل المستهدف (إذا كلاهما موجود)
        if target_section and target_class:
            if target_section.class_obj != target_class:
                errors['target_section'] = _("القسم المستهدف لا ينتمي إلى الفصل الدراسي المستهدف.")

        if errors:
            raise serializers.ValidationError(errors)

        return data
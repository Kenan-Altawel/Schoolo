# # subjects/serializers.py
# from rest_framework import serializers
# from .models import Subject
# from classes.models import Class, Section # تم التعديل بناءً على الكود الذي قدمته
# from .models import SectionSubjectRequirement # للتأكد من استيرادها

# from django.utils.translation import gettext_lazy as _

# class SubjectSerializer(serializers.ModelSerializer):
#     class_obj = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), allow_null=True, required=False,)
#     section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all(), allow_null=True, required=False,)
#     class_obj_name = serializers.CharField(source='class_obj.name', read_only=True)
#     section_name = serializers.CharField(source='section.name', read_only=True)
#     stream_type_display = serializers.CharField(source='get_stream_type_display', read_only=True)


#     class Meta:
#         model = Subject
#         fields = [
#             'id', 'name', 'description', 'stream_type', 'is_active',
#             'pdf_file', 
#             'class_obj', 'section', 
#             'class_obj_name', 'section_name', 'stream_type_display', # الحقول للقراءة فقط
#             'default_weekly_lessons', 
#             'created_at', 'updated_at'
#         ]
#         read_only_fields = ('created_at', 'updated_at')

#     def validate(self, data):
#         class_obj = data.get('class_obj')
#         section_obj = data.get('section')
#         stream_type = data.get('stream_type')
        
        
#         is_linked_to_class = class_obj is not None
#         is_linked_to_section = section_obj is not None
#         is_stream_specified = stream_type is not None

#         num_primary_links = sum([is_linked_to_class, is_linked_to_section])

#         if not is_linked_to_class and not is_linked_to_section:
#             raise serializers.ValidationError(
#                 _("المادة يجب أن ترتبط بصف دراسي (class_obj) أو شعبة محددة (section).")
#             )
#         if is_linked_to_section:
#             if not is_linked_to_class:
#                 raise serializers.ValidationError(
#                     _("عند ربط المادة بشعبة محددة (section)، يجب أيضاً تحديد الفصل الدراسي (class_obj) الذي تنتمي إليه الشعبة.")
#                 )
#             if section_obj.class_obj != class_obj:
#                 raise serializers.ValidationError({"section": _("الشعبة المحددة لا تنتمي للفصل الدراسي المدخل.")})
            
#             if is_stream_specified:
#                  raise serializers.ValidationError(
#                     _("لا يمكن تحديد نوع المسار (stream_type) عند ربط المادة بشعبة محددة (section).")
#                 )
        
#         if is_stream_specified and not is_linked_to_class:
#             raise serializers.ValidationError(
#                 _("نوع المسار (stream_type) يجب أن يُحدد فقط عند ربط المادة بصف دراسي (class_obj).")
#             )
#             if is_linked_to_section:
#                 raise serializers.ValidationError(
#                     _("لا يمكن تحديد نوع المسار (stream_type) عند ربط المادة بشعبة محددة (section) مباشرة.")
#                 )

#         default_weekly_lessons = data.get('default_weekly_lessons')
#         if default_weekly_lessons is None or default_weekly_lessons <= 0:
#             raise serializers.ValidationError(_("عدد الحصص الأسبوعية الافتراضي يجب أن يكون رقماً صحيحاً وموجباً."))

#         if is_stream_specified and stream_type not in [choice[0] for choice in Subject.STREAM_TYPE_CHOICES]:
#              raise serializers.ValidationError(_("نوع المسار المدخل غير صالح."))

#         return data


# class SectionSubjectRequirementSerializer(serializers.ModelSerializer):

#     section = serializers.PrimaryKeyRelatedField(
#         queryset=Section.objects.all(),
#     )
#     subject = serializers.PrimaryKeyRelatedField(
#         queryset=Subject.objects.all(),
#     )

#     section_name = serializers.CharField(source='section.name', read_only=True)
#     subject_name = serializers.CharField(source='subject.name', read_only=True)
#     class_name = serializers.CharField(source='section.class_obj.name', read_only=True)

#     class Meta:
#         model = SectionSubjectRequirement
#         fields = [
#             'id', 'section', 'subject', 'weekly_lessons_required',
#             'section_name', 'subject_name', 'class_name'
#         ]
#         read_only_fields = ['section_name', 'subject_name', 'class_name']



# class SubjectAssignmentSerializer(serializers.Serializer):
#     subject_id = serializers.IntegerField(
#         required=True,
#         label=_("معرف المادة")
#     )
#     weekly_hours = serializers.IntegerField(
#         required=True,
#         min_value=1, 
#         label=_("الساعات الأسبوعية")
#     )

#     def validate_subject_id(self, value):
#         if not Subject.objects.filter(id=value).exists():
#             raise serializers.ValidationError(_("المادة بهذا المعرف غير موجودة."))
#         return value
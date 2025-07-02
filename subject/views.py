# # subjects/views.py
# from rest_framework import viewsets, status
# from accounts.permissions import *
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from django.db import transaction
# from django.utils.translation import gettext_lazy as _
# from .models import Subject
# from .serializers import SubjectSerializer
# from classes.models import Class, Section 
# from .models import SectionSubjectRequirement 

# class SubjectViewSet(viewsets.ModelViewSet):
#     queryset = Subject.objects.all()
#     serializer_class = SubjectSerializer
#     permission_classes = [AllowAny] 

#     def perform_create(self, serializer):
#         with transaction.atomic():
#             subject_instance = serializer.save()
#             self._create_section_subject_requirements(subject_instance)

#     def perform_update(self, serializer):
#         with transaction.atomic():
#             subject_instance = serializer.save()
#             SectionSubjectRequirement.objects.filter(subject=subject_instance).delete()
#             self._create_section_subject_requirements(subject_instance)

#     def _create_section_subject_requirements(self, subject_instance):
#         """
#         دالة مساعدة لإنشاء سجلات SectionSubjectRequirement بناءً على
#         روابط المادة (class_obj، section، stream_type).
#         """
#         weekly_lessons = subject_instance.default_weekly_lessons

       
#         if subject_instance.section:
#             SectionSubjectRequirement.objects.create(
#                 section=subject_instance.section,
#                 subject=subject_instance,
#                 weekly_lessons_required=weekly_lessons,
#             )
#             print(f"Created SSR for specific section: {subject_instance.section.name} for subject '{subject_instance.name}'.")

#         elif subject_instance.class_obj and not subject_instance.stream_type:
#             sections_to_link = Section.objects.filter(class_obj=subject_instance.class_obj)
#             if not sections_to_link.exists():
#                 print(f"Warning: No sections found for class '{subject_instance.class_obj.name}'. No SSRs created for subject '{subject_instance.name}'.")
#                 return

#             for section in sections_to_link:
#                 if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
#                     SectionSubjectRequirement.objects.create(
#                         section=section,
#                         subject=subject_instance,
#                         weekly_lessons_required=weekly_lessons,
#                     )
#                     print(f"Created SSR for section {section.name} (General) for subject '{subject_instance.name}'.")

#         elif subject_instance.class_obj and subject_instance.stream_type:
#             sections_to_link = Section.objects.filter(
#                 class_obj=subject_instance.class_obj,
#                 stream_type=subject_instance.stream_type
#             )
#             if not sections_to_link.exists():
#                 print(f"Warning: No '{subject_instance.stream_type}' sections found for class '{subject_instance.class_obj.name}'. No SSRs created for subject '{subject_instance.name}'.")
#                 return

#             for section in sections_to_link:
#                 if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
#                     SectionSubjectRequirement.objects.create(
#                         section=section,
#                         subject=subject_instance,
#                         weekly_lessons_required=weekly_lessons,
#                     )
#                     print(f"Created SSR for section {section.name} ({subject_instance.stream_type}) for subject '{subject_instance.name}'.")

#         else:
#             print(f"Error: Subject '{subject_instance.name}' is not linked correctly (no primary link found after validation). No SectionSubjectRequirement created.")



# subject/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action # ستبقى هنا ولكن لن تستخدم لـ @action
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .models import Subject, SectionSubjectRequirement
from .serializers import SubjectSerializer, SectionSubjectRequirementSerializer
from classes.models import Class, Section
from django.db import transaction

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAdminUser] # تأكد من صلاحياتك المطلوبة

    def perform_create(self, serializer):
        with transaction.atomic():
            subject_instance = serializer.save()
            self._create_section_subject_requirements(subject_instance)

    def perform_update(self, serializer):
        with transaction.atomic():
            subject_instance = serializer.save()
            # في التحديث، من المنطقي حذف الروابط القديمة وإعادة إنشائها بناءً على العلاقات الجديدة
            SectionSubjectRequirement.objects.filter(subject=subject_instance).delete()
            self._create_section_subject_requirements(subject_instance)

    def _create_section_subject_requirements(self, subject_instance):
        """
        دالة مساعدة لإنشاء سجلات SectionSubjectRequirement بناءً على
        روابط المادة (class_obj، section، stream_type) بعد إنشاء/تحديث المادة.
        """
        weekly_lessons = subject_instance.default_weekly_lessons

        # الحالة 1: المادة مرتبطة بشعبة محددة
        if subject_instance.section:
            if not SectionSubjectRequirement.objects.filter(section=subject_instance.section, subject=subject_instance).exists():
                SectionSubjectRequirement.objects.create(
                    section=subject_instance.section,
                    subject=subject_instance,
                    weekly_lessons_required=weekly_lessons,
                )
                print(f"Created SSR for specific section: {subject_instance.section.name} for subject '{subject_instance.name}'.")
            else:
                print(f"SSR already exists for section {subject_instance.section.name} and subject '{subject_instance.name}'. Skipping creation.")

        # الحالة 2: المادة مرتبطة بصف دراسي كامل وبدون تحديد stream_type (عامة للصف)
        elif subject_instance.class_obj and not subject_instance.stream_type:
            sections_to_link = Section.objects.filter(class_obj=subject_instance.class_obj)
            if not sections_to_link.exists():
                print(f"Warning: No sections found for class '{subject_instance.class_obj.name}'. No SSRs created for subject '{subject_instance.name}'.")
                return

            for section in sections_to_link:
                if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
                    SectionSubjectRequirement.objects.create(
                        section=section,
                        subject=subject_instance,
                        weekly_lessons_required=weekly_lessons,
                    )
                    print(f"Created SSR for section {section.name} (General) for subject '{subject_instance.name}'.")
                else:
                    print(f"SSR already exists for section {section.name} and subject '{subject_instance.name}'. Skipping creation.")

        # الحالة 3: المادة مرتبطة بصف دراسي ونوع مسار معين (علمي/أدبي)
        elif subject_instance.class_obj and subject_instance.stream_type:
            sections_to_link = Section.objects.filter(
                class_obj=subject_instance.class_obj,
                stream_type=subject_instance.stream_type
            )
            if not sections_to_link.exists():
                print(f"Warning: No '{subject_instance.stream_type}' sections found for class '{subject_instance.class_obj.name}'. No SSRs created for subject '{subject_instance.name}'.")
                return

            for section in sections_to_link:
                if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
                    SectionSubjectRequirement.objects.create(
                        section=section,
                        subject=subject_instance,
                        weekly_lessons_required=weekly_lessons,
                    )
                    print(f"Created SSR for section {section.name} ({subject_instance.stream_type}) for subject '{subject_instance.name}'.")
                else:
                    print(f"SSR already exists for section {section.name} and subject '{subject_instance.name}'. Skipping creation.")

        else:
            print(f"Error: Subject '{subject_instance.name}' is not linked correctly (no valid primary link found after validation). No SectionSubjectRequirement created.")

    # >>> تم حذف جميع الـ @action's القديمة هنا. <<<
    # هذا يعني أن الـ URLs الطويلة التي لا تريدها لن يتم توليدها أو استخدامها.
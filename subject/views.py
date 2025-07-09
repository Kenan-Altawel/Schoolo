# subject/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .models import Subject, SectionSubjectRequirement
from .serializers import SubjectSerializer, SectionSubjectRequirementSerializer
from classes.models import Class, Section
from django.db import transaction
from django.db.models import Q


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        with transaction.atomic():
            subject_instance = serializer.save()
            self._create_section_subject_requirements(subject_instance)

    def perform_update(self, serializer):
        with transaction.atomic():
            subject_instance = serializer.save()
            SectionSubjectRequirement.objects.filter(subject=subject_instance).delete()
            self._create_section_subject_requirements(subject_instance)

    def _create_section_subject_requirements(self, subject_instance):
        weekly_lessons = subject_instance.default_weekly_lessons

        # 1. الأولوية للربط بشعبة محددة:
        # هذا الجزء سينفذ إذا لم يتم اعتراضه بواسطة validation السيريالايزر الجديد
        # (أي أن المادة لم تكن "عامة" وتم ربطها بشعبة محددة، وهذا لن يحدث الآن).
        if subject_instance.section:
            section = subject_instance.section
            if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
                SectionSubjectRequirement.objects.create(
                    section=section,
                    subject=subject_instance,
                    weekly_lessons_required=weekly_lessons,
                )
                print(
                    f"Created SSR for specific section: {section.name} (ID: {section.id}) for subject '{subject_instance.name}'.")
            else:
                print(
                    f"SSR already exists for specific section {section.name} and subject '{subject_instance.name}'. Skipping creation.")
            return  # إذا كانت المادة مرتبطة بشعبة محددة، ننتهي من الدالة هنا.

        # 2. الربط لصف كامل (ينفذ هذا الجزء فقط إذا لم يتم تحديد شعبة محددة للمادة).
        if subject_instance.class_obj:
            sections_to_link = Section.objects.filter(class_obj=subject_instance.class_obj)

            # **تعديل:** تعريف "المادة العامة للصف" يشمل stream_type=None أو 'General'
            is_subject_general_for_class = (subject_instance.stream_type is None) or (
                        subject_instance.stream_type == 'General')

            if not is_subject_general_for_class:  # إذا كانت المادة ليست عامة للصف (أي Scientific أو Literary)
                # اربط فقط بالشعب ذات stream_type المطابق أو الشعب العامة (stream_type is None).
                sections_to_link = sections_to_link.filter(
                    Q(stream_type=subject_instance.stream_type) | Q(stream_type__isnull=True)
                )
                print(
                    f"Linking subject '{subject_instance.name}' (Stream: {subject_instance.stream_type}) to sections in class '{subject_instance.class_obj.name}' with matching or null stream_type.")

            else:  # subject_instance.stream_type هو None أو 'General'
                # في هذه الحالة، لا يتم تطبيق أي فلترة إضافية.
                # هذا يعني أن 'sections_to_link' ستظل تحتوي على *جميع* الشعب التابعة للصف المحدد.
                print(
                    f"Linking subject '{subject_instance.name}' (General for Class) to ALL sections in class '{subject_instance.class_obj.name}'.")

            if not sections_to_link.exists():
                print(
                    f"Warning: No sections found for class '{subject_instance.class_obj.name}' matching criteria. No SSRs created for subject '{subject_instance.name}'.")
                return

            for section in sections_to_link:
                if not SectionSubjectRequirement.objects.filter(section=section, subject=subject_instance).exists():
                    SectionSubjectRequirement.objects.create(
                        section=section,
                        subject=subject_instance,
                        weekly_lessons_required=weekly_lessons,
                    )
                    print(
                        f"Created SSR for section {section.name} (ID: {section.id}) for subject '{subject_instance.name}'.")
                else:
                    print(
                        f"SSR already exists for section {section.name} and subject '{subject_instance.name}'. Skipping creation.")
        else:
            print(
                f"Error: Subject '{subject_instance.name}' is not linked to a class or specific section. No SectionSubjectRequirement created.")

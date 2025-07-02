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
from django.db.models import Q  # لاستخدام الاستعلامات المعقدة


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
            # في التحديث، من المنطقي حذف الروابط القديمة وإعادة إنشائها بناءً على العلاقات الجديدة
            SectionSubjectRequirement.objects.filter(subject=subject_instance).delete()
            self._create_section_subject_requirements(subject_instance)

    def _create_section_subject_requirements(self, subject_instance):
        """
        دالة مساعدة لإنشاء سجلات SectionSubjectRequirement بناءً على
        روابط المادة (class_obj، section، stream_type) بعد إنشاء/تحديث المادة.
        تتعامل مع جميع السيناريوهات المطلوبة.
        """
        weekly_lessons = subject_instance.default_weekly_lessons

        # إذا تم تحديد شعبة محددة للمادة، فالربط يكون لتلك الشعبة فقط.
        if subject_instance.section:
            section = subject_instance.section
            # التأكد من عدم وجود SSR مكرر (رغم أن unique_together في الموديل يمنعه)
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
            return  # انتهينا من الربط إذا كانت هناك شعبة محددة

        # إذا لم يتم تحديد شعبة محددة، فالربط يكون لصف كامل (مع أو بدون stream_type)
        if subject_instance.class_obj:
            sections_to_link = Section.objects.filter(class_obj=subject_instance.class_obj)

            # إذا تم تحديد stream_type للمادة: اربط فقط بالشعب ذات stream_type المطابق.
            if subject_instance.stream_type:
                sections_to_link = sections_to_link.filter(
                    Q(stream_type=subject_instance.stream_type) | Q(stream_type__isnull=True)
                    # الشعب ذات المسار المحدد، أو الشعب العامة
                )
                # المنطق هنا: المادة بـ stream_type محدد (مثلاً Scientific)
                # يمكن أن تُربط بالشعب التي stream_type الخاص بها إما:
                # أ) يطابق stream_type المادة (مثلاً Scientific)
                # ب) يكون None (شعبة عامة)، مما يسمح للمادة "المتخصصة" بأن تُدرس في شعبة "عامة".
                # إذا كنت تريد فقط الشعب التي يتطابق stream_type الخاص بها تماماً، فاحذف `| Q(stream_type__isnull=True)`
                # أي تكون هكذا: sections_to_link = sections_to_link.filter(stream_type=subject_instance.stream_type)

                print(
                    f"Linking subject '{subject_instance.name}' (Stream: {subject_instance.stream_type}) to sections in class '{subject_instance.class_obj.name}' with matching or null stream_type.")

            # إذا لم يتم تحديد stream_type للمادة (المادة عامة للصف): اربط بجميع الشعب في الصف.
            else:
                print(
                    f"Linking subject '{subject_instance.name}' (General) to all sections in class '{subject_instance.class_obj.name}'.")

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
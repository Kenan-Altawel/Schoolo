# subject/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .models import Subject, SectionSubjectRequirement
from .serializers import SubjectSerializer, SectionSubjectRequirementSerializer
from classes.models import Class, Section


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    def _get_weekly_lessons_value(self, item_payload_weekly_lessons=None, subject_instance=None):
        if item_payload_weekly_lessons is not None:
            return item_payload_weekly_lessons
        elif subject_instance and subject_instance.default_weekly_lessons is not None:
            return subject_instance.default_weekly_lessons
        # لم يعد هناك حاجة لـ 'else: return 1' لأن default_weekly_lessons
        # في الموديل لديه قيمة افتراضية الآن (default=1).
        return None # أو يمكنك رفع استثناء إذا كنت تتوقع قيمة دائماً

    # 1. إضافة مادة (أو مواد) لجميع شُعب صف معين:
    # POST /subjects/classes/{class_id}/assign_to_all_sections_with_details/
    @action(detail=False, methods=['post'], url_path=r'classes/(?P<class_id>\d+)/assign_to_all_sections_with_details')
    def assign_to_all_class_sections_with_details(self, request, class_id=None):
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response({"detail": _("الفصل الدراسي غير موجود.")}, status=status.HTTP_404_NOT_FOUND)

        sections_in_class = Section.objects.filter(class_obj=class_obj) # تأكد إنك فلترت الشعب لهذا الفصل فقط.
        # كانت Section.objects.all()، وهذا قد يضيف لجميع الشعب في المدرسة بغض النظر عن الفصل.

        if not sections_in_class.exists():
            return Response({"detail": _("لا توجد شعب في هذا الفصل الدراسي لإضافة متطلبات المواد إليها.")},
                            status=status.HTTP_400_BAD_REQUEST)

        payload_data = request.data
        # بما أن هذا الـ endpoint يمكن أن يستقبل ملفات، والـ request.data من نوع QueryDict (إذا كان form-data)
        # أو JSON (إذا كان application/json), يجب التعامل معها بحذر.
        # للحصول على قائمة من الكائنات إذا كانت Payload متعددة، يفضل أن يرسلها العميل كـ JSON Array في حقل واحد،
        # أو أن يتعامل الـ Viewset مع حالة أن الـ request.data نفسه هو القائمة في حالة form-data.
        # بما أننا نتعامل مع form-data، فإن request.data ليس قائمة بل هو QueryDict.
        # سنفترض أن الطلب يأتي لإنشاء مادة واحدة أو ربط مادة واحدة لكل شعبة في كل مرة.
        # إذا كنت تريد إرسال عدة مواد في نفس الطلب، ستحتاج إلى تغيير طريقة إرسال الـ payload من العميل (Postman)
        # ليكون JSON body يحتوي على قائمة، وهذا سيعارض رفع الملفات.
        # الحل الأمثل هو أن يستقبل هذا الـ action طلب واحد لمادة واحدة، أو أن تكون المادة موجودة مسبقاً.
        # إذا كنت تريد رفع ملف وإنشاء مادة جديدة مع ربطها، الأفضل أن يكون هناك endpoint خاص لإنشاء المادة فقط أولاً.

        # هنا سنفترض أن الـ request.data يحتوي على بيانات مادة واحدة (مع ملفها)
        # وأنها سيتم ربطها بكل الشعب.
        # إذا كنت ترسل قائمة من المواد، يجب أن يكون نوع الـ Content-Type هو application/json
        # ولن تتمكن من رفع الملفات مباشرة هنا.

        # تعديل جوهري هنا: التعامل مع الـ payload إذا كان form-data
        # request.data هو QueryDict ويحتوي على الملف المرفوع مباشرة (pdf_file)
        subject_name = request.data.get('name') # الاسم من الـ payload الرئيسي
        subject_stream_type = request.data.get('stream_type', 'General')
        subject_description = request.data.get('description')
        is_active = request.data.get('is_active')
        default_weekly_lessons = request.data.get('default_weekly_lessons')
        pdf_file = request.data.get('pdf_file') # استخراج الملف المرفوع

        # بناء بيانات السيريالايزر للمادة
        subject_data = {
            'name': subject_name,
            'description': subject_description,
            'stream_type': subject_stream_type,
            'is_active': is_active,
            'default_weekly_lessons': default_weekly_lessons,
            'pdf_file': pdf_file # تمرير الملف هنا!
        }

        subject_instance = None
        if subject_name:
            try:
                # محاولة جلب المادة الموجودة
                subject_instance = Subject.objects.get(name=subject_name, stream_type=subject_stream_type)
                # إذا المادة موجودة، ممكن تحتاج لتحديثها بالبيانات الجديدة بما في ذلك الملف
                # لكن بما أن السيناريو هو 'إضافة' أو 'ربط' وليس 'تحديث'، سنتركها لإنشاء جديد فقط إذا لم توجد.
                # (أو يمكنك إضافة logic هنا لتحديث المادة إذا لزم الأمر: serializer.update)
            except Subject.DoesNotExist:
                # إذا المادة غير موجودة، قم بإنشائها
                subject_serializer = SubjectSerializer(data=subject_data) # تمرير البيانات كاملة بما فيها الملف
                try:
                    subject_serializer.is_valid(raise_exception=True)
                    subject_instance = subject_serializer.save()
                except Exception as e:
                    return Response({
                        "detail": _("خطأ في إنشاء/التحقق من المادة."),
                        "error_message": str(e),
                        "serializer_errors": subject_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": _("اسم المادة (name) مفقود في الـ payload.")}, status=status.HTTP_400_BAD_REQUEST)

        if not subject_instance:
            return Response({"detail": _("لم يتم العثور على المادة أو إنشائها.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        created_requirements = []
        errors_details = []

        for section in sections_in_class:
            weekly_lessons_to_use = self._get_weekly_lessons_value(request.data.get('weekly_lessons_required'), subject_instance)

            if weekly_lessons_to_use is None: # إذا لم يتم توفير قيمة ولا توجد قيمة افتراضية
                errors_details.append({
                    "section_id": section.id,
                    "section_name": section.name,
                    "error_message": _("عدد الحصص الأسبوعية مطلوب ولم يتم توفيره للمادة ولا يوجد افتراضي."),
                    "subject_name": subject_instance.name
                })
                continue


            requirement_data = {
                'section': section.id,
                'subject': subject_instance.id,
                'weekly_lessons_required': weekly_lessons_to_use
            }
            requirement_serializer = SectionSubjectRequirementSerializer(data=requirement_data)
            try:
                requirement_serializer.is_valid(raise_exception=True)
                requirement_serializer.save()
                created_requirements.append(requirement_serializer.data)
            except Exception as e:
                errors_details.append({
                    "section_id": section.id,
                    "section_name": section.name,
                    "subject_id": subject_instance.id,
                    "subject_name": subject_instance.name,
                    "error_message": _(f"خطأ في ربط المادة بالشعبة: {str(e)}"),
                    "serializer_errors": requirement_serializer.errors
                })

        if errors_details:
            return Response(
                {"detail": _("تمت إضافة بعض المتطلبات بنجاح، وحدثت أخطاء في البعض الآخر."),
                 "created_count": len(created_requirements),
                 "created_items": created_requirements,
                 "errors": errors_details},
                status=status.HTTP_207_MULTI_STATUS
            )
        return Response(created_requirements, status=status.HTTP_201_CREATED)

    # 2. إضافة مادة (أو مواد) لشعبة محددة ضمن صف معين:
    # POST /subjects/classes/{class_id}/sections/{section_id}/assign_subject_with_details/
    @action(detail=False, methods=['post'],
            url_path=r'classes/(?P<class_id>\d+)/sections/(?P<section_id>\d+)/assign_subject_with_details')
    def assign_subject_to_specific_section_with_details(self, request, class_id=None, section_id=None):
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response({"detail": _("الفصل الدراسي غير موجود.")}, status=status.HTTP_404_NOT_FOUND)

        try:
            section_obj = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response({"detail": _("الشعبة غير موجودة.")}, status=status.HTTP_404_NOT_FOUND)

        if section_obj.class_obj != class_obj:
            return Response({"detail": _("الشعبة المحددة لا تنتمي للفصل الدراسي المدخل في الـ URL.")},
                            status=status.HTTP_400_BAD_REQUEST)

        # نفس التعديل الجوهري هنا: التعامل مع الـ payload إذا كان form-data
        subject_name = request.data.get('name')
        subject_stream_type = request.data.get('stream_type', 'General')
        subject_description = request.data.get('description')
        is_active = request.data.get('is_active')
        default_weekly_lessons = request.data.get('default_weekly_lessons')
        pdf_file = request.data.get('pdf_file') # استخراج الملف المرفوع

        subject_data = {
            'name': subject_name,
            'description': subject_description,
            'stream_type': subject_stream_type,
            'is_active': is_active,
            'default_weekly_lessons': default_weekly_lessons,
            'pdf_file': pdf_file # تمرير الملف هنا!
        }

        subject_instance = None
        if subject_name:
            try:
                subject_instance = Subject.objects.get(name=subject_name, stream_type=subject_stream_type)
            except Subject.DoesNotExist:
                subject_serializer = SubjectSerializer(data=subject_data) # تمرير البيانات كاملة بما فيها الملف
                try:
                    subject_serializer.is_valid(raise_exception=True)
                    subject_instance = subject_serializer.save()
                except Exception as e:
                    return Response({
                        "detail": _("خطأ في إنشاء/التحقق من المادة."),
                        "error_message": str(e),
                        "serializer_errors": subject_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": _("اسم المادة (name) مفقود في الـ payload.")}, status=status.HTTP_400_BAD_REQUEST)

        if not subject_instance:
            return Response({"detail": _("لم يتم العثور على المادة أو إنشائها.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        created_requirements = []
        errors_details = []

        # في هذا الـ action، بما أننا نتعامل مع شعبة واحدة محددة، فإن اللوب على الـ payload_data
        # يجب أن يكون للـ subjects، وليس لـ sections.
        # بما أننا استخرجنا بيانات مادة واحدة من request.data في بداية الدالة،
        # سنقوم بتطبيقها على هذه الشعبة الواحدة.

        weekly_lessons_to_use = self._get_weekly_lessons_value(request.data.get('weekly_lessons_required'), subject_instance)

        if weekly_lessons_to_use is None:
            errors_details.append({
                "section_id": section_obj.id,
                "section_name": section_obj.name,
                "error_message": _("عدد الحصص الأسبوعية مطلوب ولم يتم توفيره للمادة ولا يوجد افتراضي."),
                "subject_name": subject_instance.name
            })
        else:
            requirement_data = {
                'section': section_obj.id,
                'subject': subject_instance.id,
                'weekly_lessons_required': weekly_lessons_to_use
            }
            requirement_serializer = SectionSubjectRequirementSerializer(data=requirement_data)
            try:
                requirement_serializer.is_valid(raise_exception=True)
                requirement_serializer.save()
                created_requirements.append(requirement_serializer.data)
            except Exception as e:
                errors_details.append({
                    "section_id": section_obj.id,
                    "section_name": section_obj.name,
                    "subject_id": subject_instance.id,
                    "subject_name": subject_instance.name,
                    "error_message": _(f"خطأ في ربط المادة بالشعبة: {str(e)}"),
                    "serializer_errors": requirement_serializer.errors
                })


        if errors_details:
            return Response(
                {"detail": _("تمت إضافة بعض المتطلبات بنجاح، وحدثت أخطاء في البعض الآخر."),
                 "created_count": len(created_requirements),
                 "created_items": created_requirements,
                 "errors": errors_details},
                status=status.HTTP_207_MULTI_STATUS
            )
        return Response(created_requirements, status=status.HTTP_201_CREATED)


    # 3. إضافة مادة (أو مواد) لجميع شُعب قسم معين (مثل علمي/أدبي) داخل صف معين:
    # POST /subjects/classes/{class_id}/streams/{stream_type}/assign_to_sections_with_details/
    @action(detail=False, methods=['post'],
            url_path=r'classes/(?P<class_id>\d+)/streams/(?P<stream_type>[^/.]+)/assign_to_sections_with_details')
    def assign_to_stream_sections_with_details(self, request, class_id=None, stream_type=None):
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response({"detail": _("الفصل الدراسي غير موجود.")}, status=status.HTTP_404_NOT_FOUND)

        sections_in_stream = class_obj.sections_in_class.filter(stream_type=stream_type)

        if not sections_in_stream.exists():
            return Response({"detail": _(f"لا توجد شعب من نوع '{stream_type}' في هذا الفصل الدراسي لإضافة المتطلبات.")},
                            status=status.HTTP_400_BAD_REQUEST)

        # نفس التعديل الجوهري هنا: التعامل مع الـ payload إذا كان form-data
        subject_name = request.data.get('name')
        subject_stream_type_from_payload = request.data.get('stream_type', 'General') # يمكن أن يختلف عن stream_type في الـ URL
        subject_description = request.data.get('description')
        is_active = request.data.get('is_active')
        default_weekly_lessons = request.data.get('default_weekly_lessons')
        pdf_file = request.data.get('pdf_file') # استخراج الملف المرفوع

        subject_data = {
            'name': subject_name,
            'description': subject_description,
            'stream_type': subject_stream_type_from_payload, # استخدم هذا إذا كنت تريد السماح بتجاوز stream_type في الـ URL
            'is_active': is_active,
            'default_weekly_lessons': default_weekly_lessons,
            'pdf_file': pdf_file # تمرير الملف هنا!
        }

        subject_instance = None
        if subject_name:
            try:
                subject_instance = Subject.objects.get(name=subject_name, stream_type=subject_stream_type_from_payload)
            except Subject.DoesNotExist:
                subject_serializer = SubjectSerializer(data=subject_data) # تمرير البيانات كاملة بما فيها الملف
                try:
                    subject_serializer.is_valid(raise_exception=True)
                    subject_instance = subject_serializer.save()
                except Exception as e:
                    return Response({
                        "detail": _("خطأ في إنشاء/التحقق من المادة."),
                        "error_message": str(e),
                        "serializer_errors": subject_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": _("اسم المادة (name) مفقود في الـ payload.")}, status=status.HTTP_400_BAD_REQUEST)

        if not subject_instance:
            return Response({"detail": _("لم يتم العثور على المادة أو إنشائها.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        created_requirements = []
        errors_details = []

        for section in sections_in_stream:
            weekly_lessons_to_use = self._get_weekly_lessons_value(request.data.get('weekly_lessons_required'), subject_instance)

            if weekly_lessons_to_use is None:
                errors_details.append({
                    "section_id": section.id,
                    "section_name": section.name,
                    "error_message": _("عدد الحصص الأسبوعية مطلوب ولم يتم توفيره للمادة ولا يوجد افتراضي."),
                    "subject_name": subject_instance.name
                })
                continue

            requirement_data = {
                'section': section.id,
                'subject': subject_instance.id,
                'weekly_lessons_required': weekly_lessons_to_use
            }
            requirement_serializer = SectionSubjectRequirementSerializer(data=requirement_data)
            try:
                requirement_serializer.is_valid(raise_exception=True)
                requirement_serializer.save()
                created_requirements.append(requirement_serializer.data)
            except Exception as e:
                errors_details.append({
                    "section_id": section.id,
                    "section_name": section.name,
                    "subject_id": subject_instance.id,
                    "subject_name": subject_instance.name,
                    "error_message": _(f"خطأ في ربط المادة بالشعبة: {str(e)}"),
                    "serializer_errors": requirement_serializer.errors
                })

        if errors_details:
            return Response(
                {"detail": _("تمت إضافة بعض المتطلبات بنجاح، وحدثت أخطاء في البعض الآخر."),
                 "created_count": len(created_requirements),
                 "created_items": created_requirements,
                 "errors": errors_details},
                status=status.HTTP_207_MULTI_STATUS
            )
        return Response(created_requirements, status=status.HTTP_201_CREATED)
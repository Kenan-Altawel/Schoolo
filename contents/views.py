
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .serializers import SubjectContentSerializer,ContentAttachmentSerializer
from .models import ContentAttachment,SubjectContent
from rest_framework.permissions import AllowAny

class SubjectContentViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectContentSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        """
        تقوم بتصفية المحتوى بناءً على teacher_id, subject_id, و section_id
        المُرسلة كمعلمات استعلام (query parameters).
        """
        queryset = SubjectContent.objects.all()

        teacher_id = self.request.query_params.get('teacher_id', None)
        subject_id = self.request.query_params.get('subject_id', None)
        section_id = self.request.query_params.get('section_id', None)
        title_search = self.request.query_params.get('title_search', None)

        if teacher_id is not None:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        if subject_id is not None:
            queryset = queryset.filter(subject_id=subject_id)
            
        if section_id is not None:
            queryset = queryset.filter(section_id=section_id)

        if title_search is not None:
            queryset = queryset.filter(title__icontains=title_search)

            
        return queryset

   
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContentAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ContentAttachment.objects.all()
    serializer_class = ContentAttachmentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        content_id = request.data.get('content')

        if not content_id:
            return Response({"content": "SubjectContent ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subject_content_instance = SubjectContent.objects.get(id=content_id)
        except SubjectContent.DoesNotExist:
            return Response({"content": "SubjectContent with this ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        created_attachments_data = []
        errors = []

        # محاولات إنشاء المرفقات بناءً على البيانات المتوفرة في الطلب
        # يمكن إرسال multiple text_content_data أو link_url_data إذا أردت
        # (لكن يجب تعديل استخراجها من request.data.getlist() بدلاً من get())
        
        # 1. التعامل مع المرفق النصي
        text_content = request.data.get('text_content_data')
        if text_content:
            attachment_data = {
                'content': content_id,
                'attachment_type': 'text', # هنا يتم تحديد النوع بناءً على وجود text_content_data
                'text_content': text_content,
                'description': request.data.get('text_description', None)
            }
            serializer = self.get_serializer(data=attachment_data)
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save(content=subject_content_instance)
                created_attachments_data.append(serializer.data)
            except Exception as e:
                errors.append({"type": "text", "error": serializer.errors if serializer.errors else str(e)})

        # 2. التعامل مع مرفق الرابط
        link_url = request.data.get('link_url_data')
        if link_url:
            attachment_data = {
                'content': content_id,
                'attachment_type': 'link', # هنا يتم تحديد النوع بناءً على وجود link_url_data
                'link_url': link_url,
                'description': request.data.get('link_description', None)
            }
            serializer = self.get_serializer(data=attachment_data)
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save(content=subject_content_instance)
                created_attachments_data.append(serializer.data)
            except Exception as e:
                errors.append({"type": "link", "error": serializer.errors if serializer.errors else str(e)})

        # 3. التعامل مع الملفات المرفوعة
        uploaded_files = request.FILES.getlist('files')
        if uploaded_files:
            for uploaded_file in uploaded_files:
                attachment_data = {
                    'content': content_id,
                    'file': uploaded_file,
                    'description': request.data.get('file_description_general', None)
                }
                
                # استنتاج نوع المرفق بناءً على الـ Content-Type للملف
                if uploaded_file.content_type.startswith('image'):
                    attachment_data['attachment_type'] = 'image'
                elif uploaded_file.content_type.startswith('video'):
                    attachment_data['attachment_type'] = 'video'
                elif uploaded_file.content_type.startswith('audio'):
                    attachment_data['attachment_type'] = 'audio'
                else:
                    attachment_data['attachment_type'] = 'file' # نوع افتراضي للملفات الأخرى

                serializer = self.get_serializer(data=attachment_data)
                try:
                    serializer.is_valid(raise_exception=True)
                    serializer.save(content=subject_content_instance)
                    created_attachments_data.append(serializer.data)
                except Exception as e:
                    errors.append({"type": "file", "file_name": uploaded_file.name, "error": serializer.errors if serializer.errors else str(e)})

        if not created_attachments_data and not errors:
            return Response({"detail": "No valid attachment data provided."}, status=status.HTTP_400_BAD_REQUEST)

        if errors:
            return Response({
                "message": "Some attachments failed to create.",
                "created": created_attachments_data,
                "errors": errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(created_attachments_data, status=status.HTTP_201_CREATED)

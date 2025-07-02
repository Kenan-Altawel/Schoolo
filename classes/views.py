from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions 
from .models import Class, Section
from .serializers import ClassSerializer, SectionSerializer
# from subject.serializers import SubjectSerializer

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    # permission_classes = [IsSuperUser]

   
    @action(detail=True, methods=['post'], url_path='sections', serializer_class=SectionSerializer)
    # , permission_classes=[IsSuperUser]
    def create_section(self, request, pk=None):
        class_obj = self.get_object() 
        serializer = self.get_serializer(data=request.data,many=True, context={'request': request, 'class_obj': class_obj})
        serializer.is_valid(raise_exception=True)
        serializer.save() 
        return Response(serializer.data, status=status.HTTP_201_CREATED)

   
    @action(detail=True, methods=['get'], url_path='sections', serializer_class=SectionSerializer)
    # , permission_classes=[IsSuperUser]
    def list_sections(self, request, pk=None):
        class_obj = self.get_object() 
        sections = class_obj.sections.all() 
        serializer = self.get_serializer(sections, many=True)
        return Response(serializer.data)
    
    # @action(detail=True, methods=['get'], url_path='subjects', serializer_class=SubjectSerializer)
    # def list_subjects_for_class_or_stream(self, request, pk=None):
    #     class_obj = self.get_object()

    #     stream_type = request.query_params.get('stream_type', None)
    #     subjects_queryset = Subject.objects.filter(class_obj=class_obj)
    #     if stream_type:
    #         subjects_queryset = subjects_queryset.filter(stream_type=stream_type)
    #     else:
    #         subjects_queryset = subjects_queryset.filter(stream_type__isnull=True)

    #     serializer = self.get_serializer(subjects_queryset, many=True)
    #     return Response(serializer.data)

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    # permission_classes = [IsSuperUser]
    
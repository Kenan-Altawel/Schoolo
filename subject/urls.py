# # subjects/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import SubjectViewSet,IconListView

# router = DefaultRouter()
# router.register(r'subjects', SubjectViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
#     path('api/icons/', IconListView.as_view(), name='icon-list'),

#     # # /api/subjects/classes/{class_id}/assign_to_all_sections_with_details/
#     # path('subjects/classes/<int:class_id>/assign_to_all_sections_with_details/', 
#     #      SubjectViewSet.as_view({'post': 'assign_to_all_class_sections_with_details'}), 
#     #      name='subject-assign-to-all-sections-with-details'),

#     # # /api/subjects/classes/{class_id}/sections/{section_id}/assign_subject_with_details/
#     # path('subjects/classes/<int:class_id>/sections/<int:section_id>/assign_subject_with_details/', 
#     #      SubjectViewSet.as_view({'post': 'assign_subject_to_specific_section_with_details'}), 
#     #      name='subject-assign-to-specific-section-with-details'),

#     # # /api/subjects/classes/{class_id}/streams/{stream_type}/assign_to_sections_with_details/
#     # path('subjects/classes/<int:class_id>/streams/<str:stream_type>/assign_to_sections_with_details/', 
#     #      SubjectViewSet.as_view({'post': 'assign_to_stream_sections_with_details'}), 
#     #      name='subject-assign-to-stream-sections-with-details'),
# ]
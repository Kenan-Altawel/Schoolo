# subject/urls.py (لا تغييرات)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('subjects', views.SubjectViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('subjects-icons/', views.SubjectIconListView.as_view(), name='subject-icons-list'),
    path('subjects/<int:subject_id>/teachers/', views.SubjectTeachersListView.as_view(), name='subject-teachers-list'),
    path('teachers/me/taught-sections/', views.TeacherTaughtSectionsView.as_view(), name='teacher-taught-sections'),
    path('sections/<int:section_id>/subjects/',views.SectionSubjectsListView.as_view(),name='section-subjects-list'),
]

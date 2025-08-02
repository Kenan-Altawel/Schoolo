from django.urls import path
from .views import (
    SectionSubjectsListView,
    SubjectTeachersListView,
    ClassScheduleCreateView,
    ClassScheduleDetailView,
    SectionClassSchedulesView
)

urlpatterns = [
    # المسار: /api/classes/{class_id}/sections/{section_id}/subjects/
    # لعرض المواد في شعبة معينة مع عدد الحصص المضافة والمطلوبة
    path('classes/<int:class_id>/sections/<int:section_id>/subjects/',
         SectionSubjectsListView.as_view(), name='section-subjects-list'),

    # المسار: /api/subjects/{subject_id}/teachers/
    # لعرض المعلمين الذين يدرسون مادة معينة
    path('subjects/<int:subject_id>/teachers/',
         SubjectTeachersListView.as_view(), name='subject-teachers-list'),

    # المسار: /api/schedules/add/
    # لإضافة حصة جديدة (الخطوة الأخيرة بعد اختيار المعلم واليوم)
    path('schedules/add/',
         ClassScheduleCreateView.as_view(), name='class-schedule-create'),

    # المسار: /api/schedules/<int:id>/
    # لتعديل أو حذف حصة موجودة
    path('schedules/<int:id>/',
         ClassScheduleDetailView.as_view(), name='class-schedule-detail'),

    # المسار: /api/classes/{class_id}/sections/{section_id}/schedules/
    # لعرض جميع الحصص المجدولة لصف وشعبة معينين
    path('classes/<int:class_id>/sections/<int:section_id>/schedules/',
         SectionClassSchedulesView.as_view(), name='section-class-schedules'),
]

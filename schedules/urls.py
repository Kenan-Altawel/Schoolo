from django.urls import path
from .views import *

urlpatterns = [
    # المسار: /api/classes/{class_id}/sections/{section_id}/subjects/
    # لعرض المواد في شعبة معينة مع عدد الحصص المضافة والمطلوبة
    path('classes/<int:class_id>/sections/<int:section_id>/subjects/',
         SectionSubjectsListView.as_view(), name='section-subjects-list'),

    # المسار: /api/schedules/add/
    # لإضافة حصة جديدة (الخطوة الأخيرة بعد اختيار المعلم واليوم)
    path('schedules/add/',
         ClassScheduleCreateView.as_view(), name='class-schedule-create'),

    # المسار: /api/schedules/<int:id>/
    # لتعديل أو حذف حصة موجودة
    path('schedules/<int:id>/',
         ClassScheduleDetailView.as_view(), name='class-schedule-detail'),

    path('schedules/list/', ClassScheduleListView.as_view(), name='schedule-list'),
]

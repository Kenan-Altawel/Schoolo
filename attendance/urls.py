from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
    path('attendance/record/<int:section_id>/<str:date_str>/', AttendanceBulkRecordView.as_view(), name='attendance-bulk-record'),
]
# exams/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'grades', GradeViewSet, basename='grade') # تم إضافة هذا السطر

urlpatterns = [
	path('', include(router.urls)),
	path('exams/<int:pk>/conduct/', ExamConductView.as_view(), name='exam-conduct'),
	path('grades/add_section_grades/<int:exam_id>/<int:section_id>/', GradeBulkRecordView.as_view(), name='add-section-grades'),
	# path('grades/averages/activities/', ActivitiesAverageView.as_view(), name='activities-average'),
	# path('grades/averages/midterm/', MidtermAverageView.as_view(), name='midterm-average'),
	# path('grades/averages/final/', FinalScoreView.as_view(), name='final-score'),
	# path('grades/averages/total_term/', TotalTermAverageView.as_view(), name='total-term-average'),
	path('grades/averages/subject/', SubjectAverageView.as_view(), name='subject-average'),
	path('grades/averages/overall/', OverallAverageView.as_view(), name='overall-average'),
]
# academic/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'years', AcademicYearViewSet, basename='academic_year') 
router.register(r'terms', AcademicTermViewSet , basename='academic_term')
router.register(r'time-slots', TimeSlotViewSet) 
router.register(r'days-of-week', DayOfWeekViewSet)

urlpatterns = [
    path('', include(router.urls)), 
    
]
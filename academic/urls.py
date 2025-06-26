# academic/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'years', views.AcademicYearViewSet) # هذا المسار سيقبل الإنشاء المتداخل
router.register(r'terms', views.AcademicTermViewSet)
urlpatterns = [
    path('', include(router.urls)), 
    
]
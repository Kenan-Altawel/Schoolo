from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register('issues', StudentProgressionIssueViewSet, basename='progression-issue')

urlpatterns = [
    path('promote/', StudentPromotionView.as_view(), name='student-promotion'),
    path('promote/reset/', StudentPromotionResetView.as_view(), name='student-promotion-reset'),
    path('', include(router.urls)),
]
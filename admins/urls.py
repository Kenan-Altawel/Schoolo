from django.urls import path
from .views import *

urlpatterns = [
  
    path('<int:pk>/update-admin/', ManagerAdminUpdateView.as_view(), name='manager-admin-update'),
    path('<int:pk>/delete-admin/', ManagerAdminDeleteView.as_view(), name='manager-admin-delete'),
    path('show-admins/', AdminListView.as_view(), name='admins-list'),
    path('show-admins/<int:pk>/', AdminDetailView.as_view(), name='admin'),


]
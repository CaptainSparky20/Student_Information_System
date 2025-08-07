# notifications/urls.py (create this file if it doesn't exist)

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('mark_as_read/<int:pk>/', views.mark_notification_as_read, name='mark_as_read'),
]

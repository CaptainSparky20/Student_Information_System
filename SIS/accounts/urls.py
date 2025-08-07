# accounts/urls.py

from django.urls import path
from .views import unified_login

app_name = 'accounts'

urlpatterns = [
    path('login/', unified_login, name='login'),
]

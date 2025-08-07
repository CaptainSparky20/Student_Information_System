from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'student'

def redirect_to_unified_login(request):
    return redirect('accounts:login')

urlpatterns = [
    path('login/', redirect_to_unified_login, name='login'),
    path('attendance/<int:course_id>/', views.attendance_detail, name='attendance_detail'),
]

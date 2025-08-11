from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'student'

def redirect_to_unified_login(request):
    return redirect('accounts:login')

urlpatterns = [
    # Unified Login URL
    path('login/', redirect_to_unified_login, name='login'),

    path("classmates/", views.classmates_list, name="classmates"),
    path("subjects/", views.subjects_list, name="subjects"),

    # Student Dashboard Cards URLs
    path("class-overview/", views.class_overview, name="class_overview"),
    path("attendance/",views.attendance_overview,name="attendance_overview"),
    path("achievements/",views.achievements_list,name="achievements_list"),
    path("disciplinary/",views.disciplinary_list,name="disciplinary_list"),

# Class Group URLs
    path("attendance/<int:class_group_id>/", views.attendance_detail, name="attendance_detail"),
]

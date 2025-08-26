from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'adminportal'

def redirect_to_unified_login(request):
    return redirect('accounts:login')

urlpatterns = [
    # Redirect to unified login
    path('login/', redirect_to_unified_login, name='login'),

    # Lecturer management pages
    path('lecturers/', views.lecturer_list, name='lecturer_list'),
    path('lecturers/add/', views.add_lecturer, name='add_lecturer'),

    # export lecturers to CSV
    path('lecturers/export/', views.export_lecturers, name='export_lecturers'),

    # Student management pages
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/classgroups_by_department/', views.get_classgroups_by_department, name='get_classgroups_by_department'),


    #Enroll students in courses
    path('students/<int:pk>/enroll/', views.enroll_student, name='enroll_student'),
    path('classgroup/<int:pk>/edit/', views.edit_classgroup, name='edit_classgroup'),



    # Export students to CSV
    path('students/export/', views.export_students, name='export_students'),

    #staff management pages
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.add_staff, name='add_staff'),

    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),

    # course editing pages
path('classgroup/<int:pk>/assign-lecturers/', views.assign_lecturer_classgroup, name='assign_lecturer_classgroup'),
    path('courses/<int:pk>/edit/', views.edit_course, name='edit_course'),

    #coruse management pages
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.add_course, name='add_course'),
    path('classgroup/add/', views.add_classgroup, name='add_classgroup'),
    path('subject/add/', views.add_subject, name='add_subject'),

    # Export courses to CSV
    path('courses/export/', views.export_courses, name='export_courses'),
    
    #department management pages
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.add_department, name='add_department'),


    # Fee management pages
    path("fees/", views.fee_plan_list, name="fee_plan_list"),
    path("fees/new/", views.fee_plan_create, name="fee_plan_create"),
    path("fees/student/<int:student_id>/new/", views.fee_plan_create_for_student, name="fee_plan_create_for_student"),
    path("fees/plan/<int:plan_id>/", views.fee_plan_detail, name="fee_plan_detail"),
    path("fees/plan/<int:plan_id>/generate/", views.fee_plan_generate_installments, name="fee_plan_generate_installments"),
    path("fees/installment/<int:pk>/toggle/", views.installment_toggle_paid, name="installment_toggle_paid"),


]

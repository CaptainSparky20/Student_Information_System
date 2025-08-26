from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "lecturer"


def redirect_to_unified_login(request):
    return redirect("accounts:login")


urlpatterns = [
    # ===================
    # Auth & Dashboard
    # ===================
    path("login/", redirect_to_unified_login, name="login"),
    # ===================
    # Attendance (All Courses)
    # ===================
    path("attendance/", views.take_attendance, name="attendance_list"),
    path("attendance/mark/", views.mark_attendance, name="mark_attendance"),
    path(
        "attendance/mark/<int:enrollment_id>/",
        views.mark_individual_attendance,
        name="mark_individual_attendance",
    ),
    path("attendance/history/", views.attendance_history, name="attendance_history"),
    # ===================
    # ClassGroup-specific actions
    # ===================
    path(
        "classgroup/<int:classgroup_id>/attendance/",
        views.class_attendance,
        name="class_attendance",
    ),  # Summary for attendance (not the student list)
    path(
        "classgroup/<int:classgroup_id>/students/",
        views.classgroup_student_list,
        name="classgroup_student_list",
    ),  # <-- View Students
    # path('classgroup/<int:classgroup_id>/export/', views.export_class_attendance, name='export_class_attendance'),
    # ===================
    # Course-specific actions (No longer Using)
    # ===================
    path(
        "courses/<int:course_id>/attendance/",
        views.course_attendance,
        name="course_attendance",
    ),
    path(
        "courses/<int:course_id>/attendance/history/",
        views.course_attendance_history,
        name="course_attendance_history",
    ),
    path(
        "students/<int:student_id>/disciplinary-action/",
        views.take_disciplinary_action,
        name="take_disciplinary_action",
    ),
    # ===================
    # Messaging
    # ===================
    path("send-message/", views.send_message, name="send_message"),
    # ===================
    # Student-specific features
    # ===================
    path(
        "students/<int:student_id>/achievements/",
        views.student_achievements,
        name="student_achievements",
    ),
    path(
        "students/<int:student_id>/disciplinary-actions/",
        views.student_disciplinary_actions,
        name="student_disciplinary_actions",
    ),
    path(
        "students/<int:student_id>/take-disciplinary-action/",
        views.take_disciplinary_action,
        name="take_disciplinary_action",
    ),
    path(
        "students/<int:student_id>/full-details/",
        views.student_full_details,
        name="student_full_details",
    ),
    path(
        "students/<int:student_id>/update-activity/",
        views.update_student_activity,
        name="update_student_activity",
    ),
    # ===================
    # Parent-specific features
    # ===================
    path(
        "students/<int:student_id>/parents/add/",
        views.add_parent_details,
        name="add_parent_details",
    ),
    path(
        "students/<int:student_id>/parents/",
        views.manage_parents,
        name="manage_parents",
    ),
    path(
        "students/<int:student_id>/parents/<int:parent_id>/remove/",
        views.remove_parent,
        name="remove_parent",
    ),
    # ===================
    # Export CSV (per-course legacy)
    # ===================
    path("attendance/export/", views.export_attendance, name="export_attendance"),
    path(
        "classgroup/<int:classgroup_id>/export/students/",
        views.export_class_students,
        name="export_class_students",
    ),
]

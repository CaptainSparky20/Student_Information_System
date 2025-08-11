from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.db.models import Count, Q, DecimalField, F, Avg, FloatField, ExpressionWrapper
from accounts.models import CustomUser
from core.models import (
    Course,
    Lecturer,
    Student,
    Enrollment,
    Attendance,
    DisciplinaryAction,
    ClassGroup,
    StudentAchievement
)
from notifications.models import Notification

from django.urls import reverse

@login_required
def unified_dashboard(request):
    user = request.user
    context = {}

    # --- Admin Dashboard ---
    if user.role == CustomUser.Role.ADMIN:
        context.update({
            'total_lecturers': CustomUser.objects.filter(role=CustomUser.Role.LECTURER).count(),
            'total_students': CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count(),
            'total_courses': Course.objects.count(),
            'total_users': CustomUser.objects.count(),
        })

    # --- Lecturer Dashboard ---
    elif user.role == CustomUser.Role.LECTURER:
        try:
            lecturer = Lecturer.objects.get(user=user)
        except Lecturer.DoesNotExist:
            return redirect('accounts:login')
        
        classgroups = ClassGroup.objects.filter(lecturers=lecturer)
        enrollments = Enrollment.objects.filter(class_group__in=classgroups)
        today = date.today()
        # No subject in select_related!
        enrollments = enrollments.select_related('student', 'class_group')

        todays_attendance_count = Attendance.objects.filter(
            enrollment__in=enrollments,
            date=today
        ).values('enrollment__student').distinct().count()
        
        classes_data = []
        total_students = 0
        attendance_values = []

        for cg in classgroups:
            students_info = []
            for student in cg.students.all():
                enrollment = enrollments.filter(student=student, class_group=cg).first()
                attendance_records = Attendance.objects.filter(enrollment=enrollment) if enrollment else []
                total_attendance = attendance_records.count() if enrollment else 0
                present_attendance = attendance_records.filter(status='present').count() if enrollment else 0
                attendance_percentage = (present_attendance / total_attendance * 100) if total_attendance > 0 else 0
                students_info.append({
                    'student': student,
                    'email': student.user.email,
                    'full_name': student.user.get_full_name(),
                    'date_enrolled': enrollment.date_enrolled if enrollment else None,
                    'attendance_percentage': round(attendance_percentage, 2),
                    'enrollment': enrollment,
                })
                attendance_values.append(attendance_percentage)
            total_students += len(students_info)
            classes_data.append({
                'classgroup': cg,
                'students_info': students_info,
            })

        average_attendance = round(sum(attendance_values) / len(attendance_values), 2) if attendance_values else 0

        notifications = Notification.objects.filter(lecturer=user, is_read=False)
        notifications_unread_count = notifications.count()

        context.update({
            'lecturer': lecturer,
            'classes_data': classes_data,
            'notifications': notifications,
            'notifications_unread_count': notifications_unread_count,
            'total_students': total_students,
            'average_attendance': average_attendance,
            'todays_attendance_count': todays_attendance_count,
        })

    # --- Student Dashboard (CLEAN + FIXED) ---
    elif user.role == CustomUser.Role.STUDENT:
        try:
            student = Student.objects.select_related("class_group__course").get(user=user)
            student.latest_activity = timezone.now()
            student.save(update_fields=['latest_activity'])
        except Student.DoesNotExist:
            return redirect('accounts:login')

        NON_ABSENT = ("present", "late", "excused")

        # Enrollments (for cards and class list)
        enrollments_qs = (
            Enrollment.objects
            .filter(student=student)
            .select_related('class_group__course')
            .prefetch_related('class_group__lecturers__user')
        )

        # Per-class attendance (non-absent percentage)
        enrollments_list = []
        for enrollment in enrollments_qs:
            attendance_qs = Attendance.objects.filter(enrollment=enrollment)
            total = attendance_qs.count()
            present_like = attendance_qs.filter(status__in=NON_ABSENT).count()
            pct = (present_like / total * 100) if total else 0.0

            enrollments_list.append({
                'class_group': enrollment.class_group,
                'attendance_percentage': round(pct, 0),
                'enrollment': enrollment,
            })

        # Subjects count from the student's current course (if any)
        subjects_count = (
            student.class_group.course.subjects.count()
            if student.class_group and student.class_group.course_id
            else 0
        )

        # Attendance streak (consecutive non-absent sessions, newest → oldest)
        streak = 0
        for status in (
            Attendance.objects
            .filter(enrollment__student=student)
            .order_by("-date", "-session")
            .values_list("status", flat=True)
        ):
            if status in NON_ABSENT:
                streak += 1
            else:
                break

        # Achievements & disciplinary
        achievements_qs = StudentAchievement.objects.filter(student=student).order_by("-date_awarded")
        disciplinary_qs = DisciplinaryAction.objects.filter(student=student).order_by('-date')

        context.update({
            'subjects_count': subjects_count,
            'attendance_streak': streak,
            'enrollments': enrollments_list,
            'achievements': achievements_qs,
            'disciplinary_actions': disciplinary_qs,
            "profile_url_name": "dashboard:profile",
        })
        return render(request, "dashboard/dashboard.html", context)

# ========== Unified Profile View ==========

@login_required
def profile_view(request):
    user = request.user
    context = {
        "profile_url_name": "dashboard:profile",
    }

    if user.role == user.Role.STUDENT:
        try:
            student = Student.objects.select_related('user', 'class_group').prefetch_related('parents').get(user=user)
        except Student.DoesNotExist:
            student = None
        context['student'] = student

    elif user.role == user.Role.LECTURER:
        try:
            lecturer = Lecturer.objects.select_related('user', 'department').get(user=user)
        except Lecturer.DoesNotExist:
            lecturer = None
        context['lecturer'] = lecturer

    # For admin, everything is just on request.user

    return render(request, "dashboard/profile.html", context)

# ========== Unified Profile Update View ==========
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import Student, Lecturer
from accounts.models import CustomUser

@login_required
def profile_update(request):
    user = request.user
    lecturer = None
    student = None

    # Pick the right form and context for the user role
    if user.role == CustomUser.Role.ADMIN:
        from .forms import AdminProfileForm
        form_class = AdminProfileForm
        instance = user
    elif user.role == CustomUser.Role.LECTURER:
        from .forms import LecturerProfileUpdateForm
        form_class = LecturerProfileUpdateForm
        try:
            lecturer = Lecturer.objects.select_related('user', 'department').get(user=user)
        except Lecturer.DoesNotExist:
            lecturer = None
        instance = user  # form updates CustomUser
    else:
        from .forms import StudentProfileUpdateForm
        form_class = StudentProfileUpdateForm
        try:
            student = Student.objects.select_related('user', 'class_group').prefetch_related('parents').get(user=user)
        except Student.DoesNotExist:
            student = None
        instance = user  # form updates CustomUser

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            # -- REAL PROFILE PICTURE REMOVAL LOGIC --
            if request.POST.get('remove_profile_picture') == "1":
                # Only delete if there's a photo to delete
                if user.profile_picture:
                    user.profile_picture.delete(save=False)  # remove file from storage
                    user.profile_picture = None
                    user.save(update_fields=['profile_picture'])
            messages.success(request, "Profile updated successfully.")
            return redirect('dashboard:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = form_class(instance=instance)

    context = {
        "profile_url_name": "dashboard:profile",
        "form": form,
        "lecturer": lecturer,
        "student": student,
        "user": user,
    }
    return render(request, "dashboard/profile_update.html", context)

# ========== Parent Update View ==========
@login_required
def parent_update(request, pk):
    parent = get_object_or_404(Parent, pk=pk)
    # Security: only allow the parent themselves or admins to edit
    if request.user != parent.user and not request.user.is_superuser and request.user.role != request.user.Role.ADMIN:
        messages.error(request, "You are not allowed to edit this guardian.")
        return redirect('dashboard:profile')
    if request.method == "POST":
        form = ParentForm(request.POST, request.FILES, instance=parent)
        if form.is_valid():
            form.save()
            messages.success(request, "Guardian profile updated successfully.")
            return redirect('dashboard:profile')
    else:
        form = ParentForm(instance=parent)
    return render(request, "dashboard/parent_profile_update.html", {"form": form, "parent": parent})

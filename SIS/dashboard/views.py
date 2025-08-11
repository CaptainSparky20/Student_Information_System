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

# dashboard/views.py
from datetime import date
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.models import CustomUser
from core.models import (
    Course, ClassGroup, Enrollment, Attendance, Student as CoreStudent, Lecturer as CoreLecturer,
    StudentAchievement, DisciplinaryAction,
)

@login_required
def unified_dashboard(request):
    user = request.user

    # -------- Safe defaults used by dashboard.html for ALL roles --------
    context = {
        # admin defaults
        'total_lecturers': 0,
        'total_students': 0,
        'total_courses': 0,
        'total_users': 0,

        # lecturer defaults
        'lecturer': None,
        'classes_data': [],
        'notifications': [],
        'notifications_unread_count': 0,
        'total_students': 0,
        'average_attendance': 0,
        'todays_attendance_count': 0,

        # student defaults
        'subjects_count': 0,
        'attendance_streak': 0,
        'enrollments': [],
        'achievements': [],
        'disciplinary_actions': [],
        "profile_url_name": "dashboard:profile",

        # role switch for the template
        'dashboard_mode': None,
    }

    # ---------------- Admin ----------------
    if user.role == CustomUser.Role.ADMIN:
        context.update({
            'total_lecturers': CustomUser.objects.filter(role=CustomUser.Role.LECTURER).count(),
            'total_students': CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count(),
            'total_courses': Course.objects.count(),
            'total_users': CustomUser.objects.count(),
            'dashboard_mode': 'admin',
        })

    # ---------------- Lecturer ----------------
    elif user.role == CustomUser.Role.LECTURER:
        # IMPORTANT: use the *core* Lecturer model, not the accounts proxy
        lecturer = CoreLecturer.objects.filter(user=user).select_related('department').first()
        if not lecturer:
            messages.error(request, "Lecturer profile missing. Please contact admin.")
            return redirect('accounts:login')

        classgroups = ClassGroup.objects.filter(lecturers=lecturer)
        enrollments = (
            Enrollment.objects
            .filter(class_group__in=classgroups)
            .select_related('student__user', 'class_group')
        )

        today = date.today()
        todays_attendance_count = (
            Attendance.objects
            .filter(enrollment__in=enrollments, date=today)
            .values('enrollment__student').distinct().count()
        )

        classes_data, total_students, attendance_values = [], 0, []
        # Build per-class student info
        for cg in classgroups:
            students_info = []
            # cg.students is the reverse of Student.class_group (core Student model)
            for student in cg.students.select_related('user').all():
                enrollment = enrollments.filter(student=student, class_group=cg).first()
                if enrollment:
                    qs = Attendance.objects.filter(enrollment=enrollment)
                    total = qs.count()
                    present = qs.filter(status='present').count()
                    pct = (present / total * 100) if total else 0
                else:
                    pct = 0
                students_info.append({
                    'student': student,
                    'email': student.user.email,
                    'full_name': student.user.get_full_name(),
                    'date_enrolled': getattr(enrollment, "date_enrolled", None),
                    'attendance_percentage': round(pct, 2),
                    'enrollment': enrollment,
                })
                attendance_values.append(pct)

            total_students += len(students_info)
            classes_data.append({'classgroup': cg, 'students_info': students_info})

        avg_att = round(sum(attendance_values) / len(attendance_values), 2) if attendance_values else 0

        # Optional notifications (guarded)
        notifications = []
        unread = 0
        try:
            from notifications.models import Notification  # adjust or remove if you don’t have it
            notifications = Notification.objects.filter(lecturer=user, is_read=False)
            unread = notifications.count()
        except Exception:
            pass

        context.update({
            'lecturer': lecturer,
            'classes_data': classes_data,
            'notifications': notifications,
            'notifications_unread_count': unread,
            'total_students': total_students,
            'average_attendance': avg_att,
            'todays_attendance_count': todays_attendance_count,
            'dashboard_mode': 'lecturer',
        })

    # ---------------- Student ----------------
    elif user.role == CustomUser.Role.STUDENT:
        try:
            student = CoreStudent.objects.select_related("class_group__course").get(user=user)
            student.latest_activity = timezone.now()
            student.save(update_fields=['latest_activity'])
        except CoreStudent.DoesNotExist:
            messages.error(request, "Student profile missing. Please contact admin.")
            return redirect('accounts:login')

        NON_ABSENT = ("present", "late", "excused")

        enrollments_qs = (
            Enrollment.objects
            .filter(student=student)
            .select_related('class_group__course')
            .prefetch_related('class_group__lecturers__user')
        )

        enrollments_list = []
        for enrollment in enrollments_qs:
            aqs = Attendance.objects.filter(enrollment=enrollment)
            total = aqs.count()
            present_like = aqs.filter(status__in=NON_ABSENT).count()
            pct = (present_like / total * 100) if total else 0.0
            enrollments_list.append({
                'class_group': enrollment.class_group,
                'attendance_percentage': round(pct, 0),
                'enrollment': enrollment,
            })

        subjects_count = (
            student.class_group.course.subjects.count()
            if student.class_group and student.class_group.course_id
            else 0
        )

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

        achievements_qs = StudentAchievement.objects.filter(student=student).order_by("-date_awarded")
        disciplinary_qs = DisciplinaryAction.objects.filter(student=student).order_by('-date')

        context.update({
            'subjects_count': subjects_count,
            'attendance_streak': streak,
            'enrollments': enrollments_list,
            'achievements': achievements_qs,
            'disciplinary_actions': disciplinary_qs,
            'dashboard_mode': 'student',
        })

    else:
        messages.error(request, "Your account role isn’t recognized.")
        return redirect('accounts:login')

    # One way out for all roles
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

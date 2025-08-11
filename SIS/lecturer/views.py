import csv
from datetime import date, datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django import forms
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.db.models import Q

from core.models import (
    Lecturer, Course, Enrollment, Attendance,
    Student, StudentAchievement, DisciplinaryAction
)
from accounts.models import CustomUser
from accounts.decorators import role_required
from accounts.forms import LecturerProfileUpdateForm
from notifications.models import Notification
from .forms import AttendanceForm, MessageForm, AttendanceHistoryFilterForm
from core.models import ClassGroup
from .forms import DisciplinaryActionForm
from .forms import StudentAchievementForm
from core.forms import ParentForm

#==============================================================
# CLASS GROUP STUDENT LIST
# ==============================================================
@role_required(CustomUser.Role.LECTURER)
def classgroup_student_list(request, classgroup_id):
    classgroup = get_object_or_404(ClassGroup, pk=classgroup_id)
    enrollments = (
        Enrollment.objects.filter(class_group=classgroup)
        .select_related('student__user')
    )

    q = request.GET.get("q")
    if q:
        enrollments = enrollments.filter(
            Q(student__user__full_name__icontains=q) |
            Q(student__user__email__icontains=q)
        )
    students = [enrollment.student for enrollment in enrollments]

    return render(request, 'lecturer/student_list.html', {  
        'classgroup': classgroup,
        'students': students,
    })

# ==============================================================
# ATTENDANCE VIEWS (ALL COURSES & BULK)
# ==============================================================

@role_required(CustomUser.Role.LECTURER)
def take_attendance(request):
    """
    Take attendance for the lecturer's first assigned class group (bulk, by date/session).
    """
    lecturer = get_object_or_404(Lecturer, user=request.user)
    classgroups = ClassGroup.objects.filter(lecturers=lecturer)
    classgroup = classgroups.first()
    if not classgroup:
        messages.warning(request, "No class found for you.")
        return render(request, "lecturer/take_attendance.html", {})

    course = classgroup.course  # Use the related course object for display
    today = date.today()
    selected_date = (
        request.POST.get("date")
        or request.GET.get("date")
        or today.isoformat()
    )
    try:
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except Exception:
        selected_date_obj = today

    session_list = ["morning", "evening"]
    selected_session = (
        request.POST.get("session")
        or request.GET.get("session")
        or session_list[0]
    )

    enrollments = Enrollment.objects.filter(class_group=classgroup).select_related("student__user")
    attendance_qs = Attendance.objects.filter(
        enrollment__in=enrollments,
        date=selected_date_obj,
        session=selected_session
    )
    att_map = {att.enrollment_id: att for att in attendance_qs}
    for enroll in enrollments:
        att = att_map.get(enroll.id)
        enroll.attendance_selected_date = att.status if att else None
        enroll.remarks = att.description if att else ""

    statuses = ["present", "absent"]

    if request.method == "POST" and "save_attendance" in request.POST:
        updated = 0
        for enrollment in enrollments:
            status = request.POST.get(f"status_{enrollment.id}")
            remarks = request.POST.get(f"remarks_{enrollment.id}", "")
            if status in statuses:
                Attendance.objects.update_or_create(
                    enrollment=enrollment,
                    date=selected_date_obj,
                    session=selected_session,
                    defaults={"status": status, "description": remarks},
                )
                updated += 1
        messages.success(request, f"Attendance saved for {updated} students ({selected_session.capitalize()} session).")
        return redirect(f"{request.path}?date={selected_date_obj}&session={selected_session}")

    context = {
        "course": course,                 # Used for classroom display in the template
        "classgroup": classgroup,         # If you want to display class group details
        "enrollments": enrollments,
        "today": today.isoformat(),
        "selected_date": selected_date_obj.isoformat(),
        "selected_session": selected_session,
        "session_list": session_list,
        "statuses": statuses,
    }
    return render(request, "lecturer/take_attendance.html", context)


@role_required(CustomUser.Role.LECTURER)
def mark_attendance(request):
    """
    Mark attendance (single submission, old API for compatibility).
    """
    if request.method == 'POST':
        attendance_form = AttendanceForm(request.POST)
        if attendance_form.is_valid():
            enrollment = attendance_form.cleaned_data['enrollment']
            date_value = attendance_form.cleaned_data['date']
            status = attendance_form.cleaned_data['status']
            Attendance.objects.update_or_create(
                enrollment=enrollment,
                date=date_value,
                defaults={'status': status}
            )
            messages.success(request, f"Attendance updated for {enrollment.student.user.get_full_name()} on {date_value}.")
        else:
            messages.error(request, "Please correct the errors in the attendance form.")
    return redirect('lecturer:dashboard')

@role_required(CustomUser.Role.LECTURER)
def mark_individual_attendance(request, enrollment_id):
    """
    Mark individual student's attendance.
    """
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            date_value = form.cleaned_data['date']
            status = form.cleaned_data['status']
            Attendance.objects.update_or_create(
                enrollment=enrollment,
                date=date_value,
                defaults={'status': status}
            )
            messages.success(request, f"Attendance recorded for {enrollment.student.user.get_full_name()} on {date_value}.")
            return redirect('lecturer:attendance_list')
    else:
        form = AttendanceForm(initial={'enrollment': enrollment})

    return render(request, 'lecturer/mark_attendance.html', {
        'form': form,
        'enrollment': enrollment
    })

# ==============================================================
# ATTENDANCE HISTORY (PAST ATTENDANCE VIEWS)
# ==============================================================

@role_required(CustomUser.Role.LECTURER)
def class_attendance(request, classgroup_id):
    classgroup = get_object_or_404(ClassGroup, id=classgroup_id)
    enrollments = (
        Enrollment.objects.filter(class_group=classgroup)
        .select_related('student__user')
        .prefetch_related('attendance_set')
    )

    # Build a list of enrollments with attendance percentage
    enrollments_with_percent = []
    for enrollment in enrollments:
        total_attendance = enrollment.attendance_set.count()
        present_count = enrollment.attendance_set.filter(status='present').count()
        attendance_percentage = (
            round((present_count / total_attendance) * 100, 2) if total_attendance else None
        )
        enrollments_with_percent.append({
            'enrollment': enrollment,
            'attendance_percentage': attendance_percentage,
        })

    return render(request, 'lecturer/class_attendance.html', {
        'classgroup': classgroup,
        'enrollments': enrollments_with_percent,
    })

@role_required(CustomUser.Role.LECTURER)
def attendance_history(request):
    """
    View attendance records for a selected course and period.
    Shows both 'morning' and 'evening' attendance for each student, for each day in the period.
    Includes attendance stats for table display.
    """
    lecturer = get_object_or_404(Lecturer, user=request.user)

    # Find all classgroups taught by this lecturer
    classgroups = ClassGroup.objects.filter(lecturers=lecturer)
    # All courses in those classgroups
    courses = Course.objects.filter(classgroups__in=classgroups).distinct()

    session_list = ["morning", "evening"]
    period_list = ["day", "week", "month"]

    course_id = request.GET.get('course')
    date_str = request.GET.get('date')
    selected_period = request.GET.get('period', 'day')

    # Default: first course if none selected
    if not course_id and courses.exists():
        course_id = str(courses.first().id)
    selected_date = parse_date(date_str) if date_str else date.today()
    selected_course = None
    attendance_list = None
    days_range = []

    # Filter form with dynamic courses
    form = AttendanceHistoryFilterForm(
        initial={
            'course': course_id or '',
            'date': selected_date,
        },
        courses=courses
    )

    if course_id:
        try:
            selected_course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            selected_course = None

    if selected_course:
        # Get enrollments in any class group for this course
        enrollments = Enrollment.objects.filter(class_group__course=selected_course).select_related('student__user')

        # Calculate days in period
        if selected_period == "day":
            days_range = [selected_date]
        elif selected_period == "week":
            week_start = selected_date - timedelta(days=selected_date.weekday())
            days_range = [week_start + timedelta(days=i) for i in range(7)]
        elif selected_period == "month":
            month_start = selected_date.replace(day=1)
            if selected_date.month == 12:
                next_month = selected_date.replace(year=selected_date.year + 1, month=1, day=1)
            else:
                next_month = selected_date.replace(month=selected_date.month + 1, day=1)
            days_range = [month_start + timedelta(days=i) for i in range((next_month - month_start).days)]

        # Get all attendance records in this range (both sessions)
        att_filter = {
            "enrollment__in": enrollments,
            "date__range": [days_range[0], days_range[-1]],
        }
        attendance_records = Attendance.objects.filter(**att_filter).select_related('enrollment__student__user')

        # Build mapping: (enrollment_id, date, session) -> status
        attendance_map = {}
        for att in attendance_records:
            attendance_map[(att.enrollment_id, att.date, att.session)] = att.status

        attendance_list = []
        for enrollment in enrollments:
            status_by_day = []
            present_count = absent_count = late_count = excused_count = 0
            total_marked = 0
            for day in days_range:
                # Lookup both sessions for every day
                morning_status = attendance_map.get((enrollment.id, day, "morning"), "not marked")
                evening_status = attendance_map.get((enrollment.id, day, "evening"), "not marked")
                # Count stats for both sessions
                for session_status in [morning_status, evening_status]:
                    if session_status == "present":
                        present_count += 1
                        total_marked += 1
                    elif session_status == "absent":
                        absent_count += 1
                        total_marked += 1
                    elif session_status == "late":
                        late_count += 1
                        total_marked += 1
                    elif session_status == "excused":
                        excused_count += 1
                        total_marked += 1
                status_by_day.append({'date': day, 'morning': morning_status, 'evening': evening_status})
            attendance_percentage = (
                round((present_count / total_marked) * 100, 2) if total_marked else None
            )
            attendance_list.append({
                'student': enrollment.student,
                'statuses': status_by_day,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'excused_count': excused_count,
                'total_marked': total_marked,
                'attendance_percentage': attendance_percentage,
            })

    context = {
        'form': form,
        'attendance_list': attendance_list,
        'selected_course': selected_course,
        'selected_date': selected_date,
        'selected_period': selected_period,
        'session_list': session_list,
        'period_list': period_list,
        'days_range': days_range,
    }
    return render(request, 'lecturer/attendance_history.html', context)




# ==============================================================
# COURSE-SPECIFIC ATTENDANCE AND HISTORY
# ==============================================================

@role_required(CustomUser.Role.LECTURER)
def course_attendance(request, course_id):
    """
    Bulk attendance page for a specific course.
    """
    course = get_object_or_404(Course, id=course_id, lecturers__user=request.user)
    enrollments = Enrollment.objects.filter(course=course).select_related('student__user')
    today = date.today()

    if request.method == "POST":
        updated = 0
        for enrollment in enrollments:
            status = request.POST.get(f'status_{enrollment.id}')
            if status in ['present', 'absent']:
                Attendance.objects.update_or_create(
                    enrollment=enrollment,
                    date=today,
                    defaults={'status': status}
                )
                updated += 1
        if updated:
            messages.success(request, f"Attendance recorded for {updated} students in {course.name}.")
        else:
            messages.warning(request, "No attendance was marked.")
        return redirect('lecturer:course_attendance', course_id=course.id)

    return render(request, 'lecturer/course_attendance.html', {
        'course': course,
        'enrollments': enrollments,
        'today': today,
    })

@role_required(CustomUser.Role.LECTURER)
def course_attendance_history(request, course_id):
    """
    Attendance by date for a specific course.
    """
    course = get_object_or_404(Course, id=course_id, lecturers__user=request.user)
    enrollments = Enrollment.objects.filter(course=course)
    attendance_by_date = {}
    for att in Attendance.objects.filter(enrollment__in=enrollments).select_related('enrollment__student__user').order_by('-date'):
        day = att.date
        if day not in attendance_by_date:
            attendance_by_date[day] = []
        attendance_by_date[day].append(att)

    return render(request, 'lecturer/course_attendance_history.html', {
        'course': course,
        'attendance_by_date': attendance_by_date,
    })

# ==============================================================
# STUDENT & ACHIEVEMENT / DISCIPLINARY RECORD VIEWS
# ==============================================================
@role_required(CustomUser.Role.LECTURER)
def student_achievements(request, student_id):
    """
    List and add achievements for a student.
    """
    student = get_object_or_404(Student, id=student_id)
    achievements = student.achievements.order_by('-date_awarded')

    if request.method == "POST":
        form = StudentAchievementForm(request.POST)
        if form.is_valid():
            achievement = form.save(commit=False)
            achievement.student = student
            achievement.save()
            messages.success(request, "Achievement added successfully.")
            return redirect('lecturer:student_achievements', student_id=student.id)
    else:
        form = StudentAchievementForm()

    return render(request, 'lecturer/add_student_achievements.html', {
        'student': student,
        'achievements': achievements,
        'form': form,
    })

@role_required(CustomUser.Role.LECTURER)
def student_disciplinary_actions(request, student_id):
    """
    List disciplinary actions for a student.
    """
    student = get_object_or_404(Student, id=student_id)
    disciplinary_actions = DisciplinaryAction.objects.filter(student=student).order_by('-date')
    return render(request, 'lecturer/student_disciplinary_actions.html', {
        'student': student,
        'disciplinary_actions': disciplinary_actions,
    })


# ==============================================================
# TAKE DISCIPLINARY ACTION
# ==============================================================
@role_required(CustomUser.Role.LECTURER)
def take_disciplinary_action(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        form = DisciplinaryActionForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.student = student
            action.reported_by = request.user  # if you track reporter
            action.save()
            messages.success(request, "Disciplinary action recorded successfully.")
            return redirect('lecturer:student_disciplinary_actions', student_id=student.id)
    else:
        form = DisciplinaryActionForm()

    return render(request, "lecturer/take_disciplinary_action.html", {
        "student": student,
        "form": form,
    })


@role_required(CustomUser.Role.LECTURER)
def student_full_details(request, student_id):
    """
    Show full student details for lecturers.
    """
    # Fetch the Student instance with all related data in one go
    student = get_object_or_404(
        Student.objects.select_related('user')
        .prefetch_related(
            'achievements',
            'disciplinary_actions',
            'parents',
            'enrollment_set__class_group__course',
            'enrollment_set__class_group__lecturers__user'
        ),
        user__id=student_id
    )

    # Get all enrollments (class memberships) for the student
    enrollments = student.enrollment_set.select_related(
        'class_group__course'
    ).prefetch_related('class_group__lecturers__user')

    context = {
        'student_profile': student,
        'enrollments': enrollments,
    }
    return render(request, 'lecturer/student_full_details.html', context)

@role_required(CustomUser.Role.LECTURER)
def update_student_activity(request, student_id):
    """
    Update student's latest activity timestamp.
    """
    student = get_object_or_404(Student, id=student_id)
    student.latest_activity = timezone.now()
    student.save(update_fields=['latest_activity'])
    messages.success(request, f"Updated latest activity for {student.user.get_full_name()}.")
    return redirect('lecturer:student_full_details', student_id=student.id)

# ==============================================================
# ADD EMERGENCY CONTACT DETAILS 
# ==============================================================
@role_required(CustomUser.Role.LECTURER)
def add_parent_details(request, student_id):
    lecturer = get_object_or_404(Lecturer, user=request.user)
    student = get_object_or_404(Student, pk=student_id)

    if not ClassGroup.objects.filter(pk=student.class_group_id, lecturers=lecturer).exists():
        return HttpResponseForbidden("You are not authorized to manage this student.")

    if request.method == "POST":
        form = ParentForm(request.POST, request.FILES)
        if form.is_valid():
            # Basic de-dup: try name + phone
            full_name = (form.cleaned_data.get("full_name") or "").strip()
            phone = (form.cleaned_data.get("phone_number") or "").strip()
            qs = Parent.objects.filter(full_name__iexact=full_name)
            if phone:
                qs = qs.filter(phone_number__iexact=phone)
            parent = qs.first() or form.save()

            if not student.parents.filter(pk=parent.pk).exists():
                student.parents.add(parent)
                messages.success(request, "Parent/guardian saved and linked to the student.")
            else:
                messages.info(request, "This parent/guardian is already linked.")
            return redirect("lecturer:manage_parents", student_id=student.id)
        messages.error(request, "Please correct the errors below.")
    else:
        form = ParentForm()

    return render(request, "lecturer/add_parent_details.html", {"student": student, "form": form})



@role_required(CustomUser.Role.LECTURER)
def manage_parents(request, student_id):
    """
    Simple page to review all linked parents/guardians for a student
    and provide a remove action.
    """
    lecturer = get_object_or_404(Lecturer, user=request.user)
    student = get_object_or_404(Student, pk=student_id)

    if not ClassGroup.objects.filter(pk=student.class_group_id, lecturers=lecturer).exists():
        return HttpResponseForbidden("You are not authorized to view this page.")

    parents = student.parents.select_related("user")
    return render(request, "lecturer/manage_parents.html", {
        "student": student,
        "parents": parents,
    })


@role_required(CustomUser.Role.LECTURER)
def remove_parent(request, student_id, parent_id):
    """
    Unlink a parent/guardian from the student (doesn't delete the Parent profile).
    """
    lecturer = get_object_or_404(Lecturer, user=request.user)
    student = get_object_or_404(Student, pk=student_id)
    parent = get_object_or_404(Parent, pk=parent_id)

    if not ClassGroup.objects.filter(pk=student.class_group_id, lecturers=lecturer).exists():
        return HttpResponseForbidden("You are not authorized to perform this action.")

    if request.method == "POST":
        student.parents.remove(parent)
        messages.success(request, "Parent/guardian unlinked from the student.")
        return redirect("lecturer:manage_parents", student_id=student.id)

    # Gentle fallback (optional confirm page). You can skip and always POST from a button.
    messages.error(request, "Invalid request method.")
    return redirect("lecturer:manage_parents", student_id=student.id)
# ==============================================================
# MESSAGING, EXPORTS, UTILITIES
# ==============================================================

@role_required(CustomUser.Role.LECTURER)
def send_message(request):
    """
    Send notification to a student.
    """
    if request.method == 'POST':
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            student_email = message_form.cleaned_data['student_email']
            message_text = message_form.cleaned_data['message']
            try:
                student_user = CustomUser.objects.get(email=student_email, role=CustomUser.Role.STUDENT)
            except CustomUser.DoesNotExist:
                messages.error(request, "Student not found.")
            else:
                Notification.objects.create(
                    lecturer=request.user,
                    message=f"Message sent to {student_user.get_full_name()}: {message_text}"
                )
                messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Please correct the errors in the message form.")
    return redirect('lecturer:dashboard')

def export_attendance(request):
    """
    Export attendance records to CSV for a specific course and date.
    """
    course_id = request.GET.get('course')
    date_str = request.GET.get('date')

    try:
        lecturer = Lecturer.objects.get(user=request.user)
    except Lecturer.DoesNotExist:
        return HttpResponse("Not authorized", status=403)

    course = Course.objects.filter(id=course_id, lecturers=lecturer).first()
    if not course:
        return HttpResponse("Course not found or access denied", status=404)

    try:
        date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return HttpResponse("Invalid date format. Use dd-mm-yyyy.", status=400)

    enrollments = Enrollment.objects.filter(course=course).select_related('student__user')
    attendance_records = Attendance.objects.filter(
        enrollment__in=enrollments, date=date_obj
    ).select_related('enrollment__student__user')

    response = HttpResponse(content_type='text/csv')
    filename = f"attendance_{course.code}_{date_obj.strftime('%d-%m-%Y')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Email', 'Status'])

    attendance_map = {a.enrollment_id: a for a in attendance_records}

    for enrollment in enrollments:
        student = enrollment.student.user
        att = attendance_map.get(enrollment.id)
        status = att.status if att else 'not marked'
        writer.writerow([
            student.get_full_name(),
            student.email,
            status.capitalize()
        ])
    return response


# ==============================================================
# EXPORT CLASS ATTENDANCE (CSV)
# ==============================================================
@role_required(CustomUser.Role.LECTURER)
def export_class_attendance(request, classgroup_id):
    classgroup = get_object_or_404(ClassGroup, pk=classgroup_id)
    enrollments = (
        Enrollment.objects.filter(class_group=classgroup)
        .select_related('student__user')
    )
    students = [enrollment.student.user for enrollment in enrollments]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="students_{classgroup.name}.csv"'

    writer = csv.writer(response)
    writer.writerow(['#', 'Full Name', 'Email', 'Class Groups', 'Date Joined', 'Status'])

    for idx, student in enumerate(students, start=1):
        classgroups_str = ', '.join([
            e.class_group.name for e in student.student.enrollment_set.all()
        ])
        status = 'Active' if student.is_active else 'Inactive'
        writer.writerow([
            idx,
            student.get_full_name(),
            student.email,
            classgroups_str,
            student.date_joined.strftime('%Y-%m-%d'),
            status
        ])
    return response


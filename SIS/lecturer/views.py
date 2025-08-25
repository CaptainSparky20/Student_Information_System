import csv, re
from datetime import date, datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django import forms
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.db.models import Q, Prefetch

from core.models import (
    Lecturer, Course, Enrollment, Attendance,
    Student, StudentAchievement, DisciplinaryAction
)
from accounts.models import CustomUser
from accounts.decorators import role_required
from accounts.forms import LecturerProfileUpdateForm
from notifications.models import Notification
from .forms import AttendanceForm, MessageForm, AttendanceHistoryFilterForm, DisciplinaryActionForm
from core.models import ClassGroup
from .forms import StudentAchievementForm
from core.forms import ParentForm
from django.http import HttpResponseForbidden 
from core.models import Parent


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
    lecturer = get_object_or_404(Lecturer, user=request.user)

    # All classgroups assigned to this lecturer
    classgroups = (
        ClassGroup.objects
        .filter(lecturers=lecturer)
        .select_related("course")
        .order_by("course__name", "name")
        .distinct()
    )

    period_list = ["day", "week", "month"]
    selected_period = request.GET.get("period", "day")
    if selected_period not in period_list:
        selected_period = "day"

    # read classgroup from querystring
    classgroup_id = request.GET.get("classgroup")
    selected_date = parse_date(request.GET.get("date") or "") or date.today()

    # default to the first classgroup if none chosen
    if not classgroup_id and classgroups.exists():
        classgroup_id = str(classgroups.first().id)

    # resolve selected_classgroup ONLY from lecturer's list
    selected_classgroup = classgroups.filter(id=classgroup_id).first() if classgroup_id else None

    attendance_list, days_range = None, []

    # (optional) form wiring, if you have one
    try:
        from lecturer.forms import AttendanceHistoryFilterForm
        form = AttendanceHistoryFilterForm(
            initial={"class_group": classgroup_id or "", "date": selected_date},
            classgroups=classgroups,  # <— pass lecturer’s classgroups here
        )
    except Exception:
        form = None

    if selected_classgroup:
        # enrollments for this classgroup only
        enrollments = (Enrollment.objects
            .filter(class_group=selected_classgroup)
            .select_related("student__user", "class_group")
            .order_by("student__user__full_name", "student__user__id")
        )

        # build date range
        if selected_period == "day":
            days_range = [selected_date]
        elif selected_period == "week":
            start = selected_date - timedelta(days=selected_date.weekday())
            days_range = [start + timedelta(days=i) for i in range(7)]
        else:  # month
            m1 = selected_date.replace(day=1)
            m2 = (m1.replace(year=m1.year + 1, month=1) if m1.month == 12
                  else m1.replace(month=m1.month + 1))
            days_range = [m1 + timedelta(days=i) for i in range((m2 - m1).days)]

        if days_range:
            records = (Attendance.objects
                .filter(enrollment__in=enrollments, date__range=[days_range[0], days_range[-1]])
                .select_related("enrollment__student__user")
                .only("enrollment_id", "date", "session", "status")
            )
            att = {(r.enrollment_id, r.date, r.session): r.status for r in records}

            attendance_list = []
            for e in enrollments:
                row, present, absent, late, excused, total = [], 0, 0, 0, 0, 0
                for d in days_range:
                    m = att.get((e.id, d, "morning"), "not marked")
                    v = att.get((e.id, d, "evening"), "not marked")
                    for s in (m, v):
                        if s in ("present", "absent", "late", "excused"): total += 1
                        if s == "present": present += 1
                        elif s == "absent": absent += 1
                        elif s == "late": late += 1
                        elif s == "excused": excused += 1
                    row.append({"date": d, "morning": m, "evening": v})
                pct = round((present / total) * 100, 2) if total else None
                attendance_list.append({
                    "student": e.student,
                    "statuses": row,
                    "present_count": present,
                    "absent_count": absent,
                    "late_count": late,
                    "excused_count": excused,
                    "total_marked": total,
                    "attendance_percentage": pct,
                })

    context = {
        "form": form,
        "classgroups": classgroups,              # ✅ template fallback
        "selected_classgroup": selected_classgroup,
        "attendance_list": attendance_list,
        "selected_date": selected_date,
        "selected_period": selected_period,
        "period_list": period_list,
        "days_range": days_range,
    }
    return render(request, "lecturer/attendance_history.html", context)




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
    Accepts either Student.pk or the related CustomUser.pk in the URL.
    """

    enrollments_qs = (
        Enrollment.objects
        .select_related("class_group__course")
        .prefetch_related("class_group__lecturers__user")
    )

    student = get_object_or_404(
        Student.objects
        .select_related("user", "class_group__course", "class_group__department")
        .prefetch_related(
            "parents",
            Prefetch("achievements", queryset=StudentAchievement.objects.order_by("-date_awarded")),
            Prefetch("disciplinary_actions", queryset=DisciplinaryAction.objects.order_by("-date")),
            Prefetch("enrollment_set", queryset=enrollments_qs, to_attr="prefetched_enrollments"),
        )
        .filter(
            Q(pk=student_id) | Q(user__id=student_id),        # <— support both ids
            user__role=CustomUser.Role.STUDENT
        )
    )

    context = {
        "student_profile": student,
        "enrollments": getattr(student, "prefetched_enrollments", []),
    }
    return render(request, "lecturer/student_full_details.html", context)

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
    lecturer = get_object_or_404(Lecturer, user=request.user)
    student = get_object_or_404(Student, pk=student_id)

    if not ClassGroup.objects.filter(pk=student.class_group_id, lecturers=lecturer).exists():
        return HttpResponseForbidden("You are not authorized to view this page.")

    parents = student.parents.all()
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
    filename = f"attendance_{course.code}_{date_obj.strftime('%d/%m/%y')}.csv"
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

def _parse_any_date(s: str | None) -> date:
    if not s:
        return date.today()
    d = parse_date(s)  # try ISO first
    if d:
        return d
    try:  # try DD-MM-YYYY
        return datetime.strptime(s, "%d-%m-%Y").date()
    except Exception:
        return date.today()


@role_required(CustomUser.Role.LECTURER)
def export_attendance(request):
    lecturer = get_object_or_404(Lecturer, user=request.user)
    classgroup_id = request.GET.get("classgroup")
    if not classgroup_id:
        return HttpResponse("Missing ?classgroup", status=400)

    classgroup = (
        ClassGroup.objects.filter(id=classgroup_id, lecturers=lecturer)
        .select_related("course")
        .first()
    )
    if not classgroup:
        return HttpResponse("Class group not found or access denied.", status=403)

    period = request.GET.get("period", "day")
    period = period if period in {"day", "week", "month", "all"} else "day"
    ref_date = _parse_any_date(request.GET.get("date"))

    if period == "day":
        days_range = [ref_date]
    elif period == "week":
        start = ref_date - timedelta(days=ref_date.weekday())
        days_range = [start + timedelta(days=i) for i in range(7)]
    elif period == "month":
        m1 = ref_date.replace(day=1)
        m2 = m1.replace(year=m1.year + 1, month=1) if m1.month == 12 else m1.replace(month=m1.month + 1)
        days_range = [m1 + timedelta(days=i) for i in range((m2 - m1).days)]
    else:
        enrollments_qs = Enrollment.objects.filter(class_group=classgroup)
        att_qs = Attendance.objects.filter(enrollment__in=enrollments_qs).only("date")
        first = att_qs.order_by("date").first()
        last = att_qs.order_by("-date").first()
        if not first or not last:
            days_range = [date.today()]
        else:
            span = (last.date - first.date).days + 1
            days_range = [first.date + timedelta(days=i) for i in range(span)]

    enrollments = (
        Enrollment.objects
        .filter(class_group=classgroup)
        .select_related("student__user", "class_group")
        .order_by("student__user__full_name", "student__user__id")
    )

    sessions = ("morning", "evening")

    att_records = (
        Attendance.objects
        .filter(enrollment__in=enrollments, date__range=[days_range[0], days_range[-1]])
        .select_related("enrollment__student__user")
        .only("enrollment_id", "date", "session", "status", "description")
    )
    att_map = {(r.enrollment_id, r.date, r.session): r for r in att_records}

    # --- CSV response ---
    base = f"{classgroup.name}"
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    if period == "day":
        suffix = ref_date.strftime("%Y-%m-%d")
    elif period == "week":
        week_start = (ref_date - timedelta(days=ref_date.weekday())).strftime("%Y-%m-%d")
        week_end = (parse_date(week_start) + timedelta(days=6)).strftime("%Y-%m-%d")
        suffix = f"week_{week_start}_to_{week_end}"
    elif period == "month":
        suffix = ref_date.strftime("month_%Y-%m")
    else:
        suffix = "all"

    filename = f"attendance_{base}_{suffix}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    # Header
    writer.writerow([
        "Student Name",
        "Email",
        "Class Group",
        "Date",      # dd/mm/yy in rows
        "Session",
        "Status",
        "Notes",
    ])

    # Rows
    for e in enrollments:
        student_user = e.student.user
        for d in days_range:
            for s in sessions:
                rec = att_map.get((e.id, d, s))
                status = rec.status if rec else "not marked"
                notes = rec.description if rec and rec.description else ""
                writer.writerow([
                    student_user.get_full_name(),
                    student_user.email,
                    classgroup.name,
                    d.strftime("%d/%m/%y"),  # <-- updated format
                    s.title(),
                    status.title() if status != "not marked" else "n/a",
                    notes,
                ])

    return response



@role_required(CustomUser.Role.LECTURER)
def export_class_students(request, classgroup_id):
    """
    Export the students of a class group (and related fields) as CSV.
    - One row per student enrolled in the class group.
    - Dates are formatted as dd/mm/yy.
    """
    lecturer = get_object_or_404(Lecturer, user=request.user)
    classgroup = (
        ClassGroup.objects
        .filter(id=classgroup_id, lecturers=lecturer)
        .select_related("course", "department")
        .first()
    )
    if not classgroup:
        return HttpResponse("Class group not found or access denied.", status=403)

    # Pull enrollments for THIS class group only, with all useful relations
    enrollments = (
        Enrollment.objects
        .filter(class_group=classgroup)
        .select_related(
            "student__user",
            "class_group__course",
            "class_group__department",
        )
        .prefetch_related("student__parents")
        .order_by("student__user__full_name", "student__user__id")
    )

    # CSV response setup
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", classgroup.name).strip("_") or "class"
    today_str = timezone.localdate().strftime("%Y-%m-%d")  # keep filename ISO for sorting
    filename = f"students_{base}_{today_str}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    # Header
    writer.writerow([
        "Full Name",
        "Email",
        "IC Number",
        "Phone",
        "Active",
        "Class Group",
        "Course",
        "Department",
        "Date Enrolled (Class)",   # dd/mm/yy
        "User Date Joined",        # dd/mm/yy
        "Emergency Name",
        "Emergency Relation",
        "Emergency Phone",
        "Parent Names",
        "Parent Roles",
        "Parent Phones",
        "Parent Emails",
    ])

    # Date format required
    dfmt = "%d/%m/%y"

    # Rows
    for e in enrollments:
        stu = e.student
        u = stu.user
        parents = list(stu.parents.all())

        parent_names = "; ".join(filter(None, [p.full_name for p in parents]))
        parent_roles = "; ".join(filter(None, [", ".join(p.get_roles_list()) for p in parents]))
        parent_phones = "; ".join(filter(None, [p.phone_number for p in parents]))
        parent_emails = "; ".join(filter(None, [p.email for p in parents]))

        writer.writerow([
            u.get_full_name(),
            u.email,
            u.identity_card_number,
            u.phone_number or "",
            "Yes" if u.is_active else "No",
            classgroup.name,
            classgroup.course.name if classgroup.course else "",
            classgroup.department.name if classgroup.department else "",
            e.date_enrolled.strftime(dfmt) if e.date_enrolled else "",
            u.date_joined.strftime(dfmt) if u.date_joined else "",
            stu.emergency_name or "",
            stu.emergency_relation or "",
            stu.emergency_phone or "",
            parent_names,
            parent_roles,
            parent_phones,
            parent_emails,
        ])

    return response
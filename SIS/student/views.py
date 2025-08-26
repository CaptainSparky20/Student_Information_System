from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from accounts.models import CustomUser
from accounts.forms import StudentProfileUpdateForm
from core.models import (
    Enrollment,
    Attendance,
    Course,
    ClassGroup,
    Student,
    DisciplinaryAction,
    StudentAchievement,
    Subject,
    Lecturer,
)
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Prefetch
import calendar
from collections import defaultdict, OrderedDict
from datetime import date


@role_required(CustomUser.Role.STUDENT)
def class_overview(request):
    """Student view: show class meta, subjects, lecturers, and classmates."""
    # student + class
    student = get_object_or_404(
        Student.objects.select_related("user"), user=request.user
    )
    class_group = student.class_group

    # handle students without a class
    if not class_group:
        return render(
            request,
            "student/class_overview.html",
            {
                "class_group": None,
                "subjects": [],
                "subj_to_lects": {},  # kept for compatibility
                "classmates": [],
            },
        )

    # subjects for this class' course, with lecturers+users prefetched
    subjects = []
    subj_to_lects = {}
    if class_group.course_id:
        subjects = (
            class_group.course.subjects.select_related("course")
            .prefetch_related(
                Prefetch("lecturers", queryset=Lecturer.objects.select_related("user"))
            )
            .all()
        )
        # keep the mapping for compatibility, even though template can iterate directly
        for s in subjects:
            subj_to_lects[s.id] = list(s.lecturers.all())

    # classmates (exclude self), bring along the linked user for names/emails/pictures
    classmates = (
        Student.objects.filter(class_group=class_group)
        .exclude(pk=student.pk)
        .select_related("user")
        .order_by("user__full_name", "user__email")
    )

    context = {
        "class_group": class_group,
        "subjects": subjects,
        "subj_to_lects": subj_to_lects,
        "classmates": classmates,
    }
    return render(request, "student/class_overview.html", context)


@login_required
def attendance_overview(request):
    if not _require_student(request.user):
        return redirect("accounts:login")
    student = Student.objects.get(user=request.user)
    enrollments = Enrollment.objects.filter(student=student).select_related(
        "class_group"
    )

    # Per-enrollment attendance + overall average
    per_class = []
    all_present, all_total = 0, 0
    for enr in enrollments:
        qs = Attendance.objects.filter(enrollment=enr)
        total = qs.count()
        present = qs.filter(status="present").count()
        pct = round((present / total) * 100, 2) if total else 0.0
        per_class.append(
            {
                "class_group": enr.class_group,
                "present": present,
                "total": total,
                "percentage": pct,
            }
        )
        all_present += present
        all_total += total

    avg_attendance = round((all_present / all_total) * 100, 2) if all_total else 0.0

    context = {
        "student": student,
        "per_class": per_class,
        "avg_attendance": avg_attendance,
    }
    return render(request, "student/attendance.html", context)


@role_required(CustomUser.Role.STUDENT)
def achievements_list(request):
    student = Student.objects.get(user=request.user)
    achievements = StudentAchievement.objects.filter(student=student).order_by(
        "-date_awarded"
    )
    return render(
        request,
        "student/achievements.html",
        {
            "student": student,
            "achievements": achievements,
            "total_achievements": achievements.count(),
        },
    )


@role_required(CustomUser.Role.STUDENT)
def disciplinary_list(request):
    student = Student.objects.get(user=request.user)
    actions = DisciplinaryAction.objects.filter(student=student).order_by("-date")
    return render(
        request,
        "student/disciplinary.html",
        {
            "student": student,
            "actions": actions,
            "total_actions": actions.count(),
        },
    )


@role_required(CustomUser.Role.STUDENT)
def attendance_detail(request, class_group_id):
    # --- Who & where ---
    student = get_object_or_404(Student, user=request.user)
    class_group = get_object_or_404(ClassGroup, id=class_group_id)
    enrollment = get_object_or_404(Enrollment, student=student, class_group=class_group)

    # --- Records (one per date+session) ---
    attendance_qs = Attendance.objects.filter(enrollment=enrollment).order_by(
        "-date", "-session"
    )

    # --- Quick stats ---
    total_classes = attendance_qs.count()
    absences = attendance_qs.filter(status="absent").count()
    attended_classes = total_classes - absences  # treat non-absent as attended
    attendance_percentage = (
        round((attended_classes / total_classes) * 100, 1) if total_classes else 0
    )

    # --- Table rows: combine AM/PM into one row per date ---
    daily_map = (
        OrderedDict()
    )  # {date: {"date": d, "morning": Attendance|None, "evening": Attendance|None}}
    for rec in attendance_qs:
        d = rec.date
        if d not in daily_map:
            daily_map[d] = {"date": d, "morning": None, "evening": None}
        if rec.session == "morning":
            daily_map[d]["morning"] = rec
        elif rec.session == "evening":
            daily_map[d]["evening"] = rec
    daily_rows = list(daily_map.values())  # keeps ordering (desc by date)

    # --- Toggle + calendar month params ---
    mode = request.GET.get("mode", "table")  # 'table' or 'calendar'
    today = date.today()
    y = int(request.GET.get("y", today.year))
    m = int(request.GET.get("m", today.month))

    cal = calendar.Calendar(firstweekday=0)  # Monday = 0
    raw_weeks = cal.monthdatescalendar(y, m)  # list[list[date]]

    # --- Build month map with AM/PM objects for each visible day ---
    by_date_sessions = defaultdict(lambda: {"morning": None, "evening": None})
    month_records = attendance_qs.filter(date__year=y, date__month=m)
    for r in month_records:
        if r.session == "morning":
            by_date_sessions[r.date]["morning"] = r
        elif r.session == "evening":
            by_date_sessions[r.date]["evening"] = r

    # --- Calendar cells: include AM/PM objects directly ---
    weeks_data = []
    for wk in raw_weeks:
        row = []
        for d in wk:
            sess = by_date_sessions.get(d, {"morning": None, "evening": None})
            row.append(
                {
                    "date": d,
                    "in_month": (d.month == m),
                    "is_today": (d == today),
                    "morning": sess["morning"],
                    "evening": sess["evening"],
                }
            )
        weeks_data.append(row)

    # --- Prev/next month ---
    prev_y, prev_m = (y - 1, 12) if m == 1 else (y, m - 1)
    next_y, next_m = (y + 1, 1) if m == 12 else (y, m + 1)

    # --- Context ---
    context = {
        "class_group": class_group,
        "attendance_records": attendance_qs,  # still available if needed elsewhere
        "daily_rows": daily_rows,
        "total_classes": total_classes,
        "attended_classes": attended_classes,
        "attendance_percentage": attendance_percentage,
        "absences": absences,
        # toggle + calendar
        "mode": mode,
        "year": y,
        "month": m,
        "month_name": calendar.month_name[m],
        "weeks_data": weeks_data,
        "prev_y": prev_y,
        "prev_m": prev_m,
        "next_y": next_y,
        "next_m": next_m,
        "today": today,
    }

    return render(request, "student/attendance_details.html", context)


@role_required(CustomUser.Role.STUDENT)
def classmates_list(request):
    me = get_object_or_404(Student, user=request.user)
    class_group = me.class_group
    classmates = []
    if class_group_id := getattr(class_group, "id", None):
        classmates = (
            Student.objects.filter(class_group_id=class_group_id)
            .select_related("user")
            .order_by("user__short_name", "user__full_name")
        )
    return render(
        request,
        "student/classmates_list.html",
        {
            "me": me,
            "class_group": class_group,
            "classmates": classmates,
        },
    )


@role_required(CustomUser.Role.STUDENT)
def subjects_list(request):
    me = get_object_or_404(Student, user=request.user)
    class_group = me.class_group
    subjects = []
    subj_to_lects = {}
    if class_group and class_group.course_id:
        subjects = (
            class_group.course.subjects.all().select_related("course").order_by("code")
        )
        # Subject.lecturers exists (M2M), build mapping for chips
        for s in subjects:
            subj_to_lects[s.id] = list(s.lecturers.select_related("user").all())
    return render(
        request,
        "student/subjects_list.html",
        {
            "me": me,
            "class_group": class_group,
            "subjects": subjects,
            "subj_to_lects": subj_to_lects,
        },
    )

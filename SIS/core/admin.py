from django.contrib import admin
from .models import (
    Lecturer,
    Student,
    Course,
    Subject,
    ClassGroup,
    Enrollment,
    Attendance,
    StudentAchievement,
    DisciplinaryAction,
    Department,
    Parent,
    StudentFeePlan,
    StudentFeeInstallment,
)


# ---------- Lecturer ----------
@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "profile_picture_display")
    readonly_fields = ("profile_picture_display",)
    filter_horizontal = ("subjects",)

    def profile_picture_display(self, obj):
        if obj.profile_picture:
            from django.utils.html import format_html

            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:50%;" />',
                obj.profile_picture.url,
            )
        return "-"

    profile_picture_display.short_description = "Profile Picture"


# ---------- Student ----------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "class_group", "profile_picture_display", "latest_activity")
    readonly_fields = ("profile_picture_display",)

    def profile_picture_display(self, obj):
        if obj.profile_picture:
            from django.utils.html import format_html

            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:50%;" />',
                obj.profile_picture.url,
            )
        return "-"

    profile_picture_display.short_description = "Profile Picture"


# ---------- Course ----------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "department", "description")
    search_fields = ("name", "code")
    list_filter = ("department",)


# ---------- Subject ----------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "course", "description")
    search_fields = ("name", "code")
    list_filter = ("course",)


# ---------- ClassGroup ----------
@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "course",
        "department",
        "year",
        "classroom",
        "get_lecturers",
    )
    list_filter = ("department", "course", "year")
    search_fields = ("name", "classroom")
    filter_horizontal = ("lecturers",)  # <-- This lets you assign multiple lecturers

    def get_lecturers(self, obj):
        return ", ".join([str(lecturer) for lecturer in obj.lecturers.all()])

    get_lecturers.short_description = "Lecturers"


# ---------- Enrollment ----------
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "class_group", "date_enrolled")
    list_filter = ("class_group",)


# ---------- Attendance ----------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "date", "session", "status", "description")
    list_filter = ("date", "session", "status")
    search_fields = (
        "enrollment__student__user__full_name",
        "enrollment__student__user__short_name",
    )


# ---------- Student Achievement ----------
@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "date_awarded")
    list_filter = ("date_awarded",)


# ---------- Disciplinary Action ----------
@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = ("student", "action", "date")
    list_filter = ("date",)


# ---------- Department ----------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)


# ---------- Parent ----------
@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone_number", "occupation")
    search_fields = ("full_name", "email", "phone_number")


# ---------- Student Fee Plan and Installments ----------
class StudentFeeInstallmentInline(admin.TabularInline):
    model = StudentFeeInstallment
    extra = 0
    fields = ("sequence_no", "due_date", "amount", "is_paid", "paid_date", "note")
    readonly_fields = ("sequence_no", "amount")
    ordering = ("sequence_no",)


@admin.register(StudentFeePlan)
class StudentFeePlanAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "total_amount",
        "months",
        "monthly_amount_display",
        "start_date",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "start_date",
    )
    search_fields = ("student__user__full_name", "student__user__email", "description")
    inlines = [StudentFeeInstallmentInline]
    actions = ["generate_installments"]

    def monthly_amount_display(self, obj):
        return obj.monthly_amount

    monthly_amount_display.short_description = "Monthly Amount"

    @admin.action(description="Generate monthly installments")
    def generate_installments(self, request, queryset):
        total_created = 0
        for plan in queryset:
            total_created += plan.ensure_installments()  # see model method below
        self.message_user(
            request,
            f"Installments generated/updated for {queryset.count()} plan(s). ({total_created} rows affected)",
        )

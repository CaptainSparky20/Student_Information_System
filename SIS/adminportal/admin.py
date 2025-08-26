from django.contrib import admin
from accounts.models import Lecturer, Student


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ["email", "full_name", "short_name", "department"]
    search_fields = ["email", "full_name", "short_name", "department"]
    ordering = ["full_name", "short_name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["email", "full_name", "short_name"]
    search_fields = ["email", "full_name", "short_name"]
    ordering = ["full_name", "short_name"]

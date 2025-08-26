from django import forms
from accounts.models import CustomUser
from core.models import Department, Student, Course, Subject, ClassGroup, Lecturer


# ---------- ADMIN PROFILE FORM ----------
class AdminProfileForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="Select Department",
        widget=forms.Select(
            attrs={
                "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = ["full_name", "short_name", "email", "department", "profile_picture"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                    "placeholder": "Enter your full name",
                }
            ),
            "short_name": forms.TextInput(
                attrs={
                    "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                    "placeholder": "Enter your short name (e.g. Ali)",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full border border-gray-300 rounded px-4 py-2 bg-gray-100 cursor-not-allowed",
                    "readonly": "readonly",
                    "placeholder": "Your email address",
                }
            ),
            "profile_picture": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-2 bg-white/10 rounded border border-white/20 text-white",
                    "accept": "image/*",
                }
            ),
        }


# ---------- LECTURER PROFILE FORM ----------


class LecturerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "profile_picture",
            "full_name",
            "short_name",
            "phone_number",
            "department",
            "address",
        ]
        widgets = {
            "profile_picture": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-2 bg-white/10 rounded border border-white/20 text-white",
                    "accept": "image/*",
                }
            ),
            "full_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 text-white border border-white/20",
                    "placeholder": "Full Name",
                }
            ),
            "short_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 text-white border border-white/20",
                    "placeholder": "Short Name",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 text-white border border-white/20",
                    "placeholder": "First Name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 text-white border border-white/20",
                    "placeholder": "Last Name",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 text-white border border-white/20",
                    "placeholder": "Phone number",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 text-white border border-white/20"
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 text-white border border-white/20",
                    "placeholder": "Address",
                    "rows": 2,
                }
            ),
        }


# ---Student Profile Update Form---


class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "full_name",
            "short_name",
            "identity_card_number",
            "email",
            "phone_number",
            "address",
            "profile_picture",
        ]
        widgets = {
            "email": forms.EmailInput(attrs={"readonly": "readonly"}),
            "identity_card_number": forms.TextInput(attrs={"readonly": "readonly"}),
            "profile_picture": forms.FileInput(),
            "address": forms.Textarea(attrs={"rows": 2}),
        }


# Student-only fields (date of birth, emergency contact, class group)
class StudentExtraProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "date_of_birth",
            "class_group",  # Will be read-only in template
            "emergency_name",
            "emergency_relation",
            "emergency_phone",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "class_group": forms.Select(attrs={"disabled": "disabled"}),
        }

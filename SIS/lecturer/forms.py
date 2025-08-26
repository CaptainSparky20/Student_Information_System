from django import forms
from accounts.models import CustomUser
from core.models import (
    Course,
    Student,
    Enrollment,
    DisciplinaryAction,
    Course,
    ClassGroup,
)


# ---------- Lecturer Login Form ----------
class LecturerLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                "placeholder": "Enter your email",
            }
        ),
        label="Email",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                "placeholder": "Enter your password",
            }
        ),
        label="Password",
    )


# ---------- Lecturer Profile Update Form ----------
class LecturerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["full_name", "short_name", "department", "phone_number", "address"]
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
            "department": forms.Select(
                attrs={
                    "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                    "placeholder": "Enter your phone number",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                    "placeholder": "Enter your address",
                    "rows": 3,
                }
            ),
        }


# ---------- Attendance Form ----------
class AttendanceForm(forms.Form):
    enrollment = forms.ModelChoiceField(
        queryset=Enrollment.objects.all(), widget=forms.HiddenInput()
    )
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full border border-gray-300 rounded px-4 py-2",
            }
        ),
        label="Date",
    )
    status = forms.ChoiceField(
        choices=[
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
            ("excused", "Excused"),
        ],
        widget=forms.RadioSelect,
        label="Status",
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "E.g., Left early, MC",
                "class": "w-full border border-gray-300 rounded px-4 py-2",
            }
        ),
        label="Remarks",
    )


# ---------- Message Form ----------
class MessageForm(forms.Form):
    student_email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                "placeholder": "Student email",
            }
        ),
        label="Student Email",
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600",
                "placeholder": "Type your message here...",
                "rows": 4,
            }
        ),
        label="Message",
    )


# ---------- Attendance History Filter Form ----------
class AttendanceHistoryFilterForm(forms.Form):
    class_group = forms.ModelChoiceField(
        queryset=ClassGroup.objects.none(),
        required=False,
        label="Class Group",
        widget=forms.Select(attrs={"class": "text-white bg-gray-800 rounded p-2"}),
    )
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "class": "text-white bg-gray-800 rounded p-2"}
        ),
        required=False,
        label="Date",
    )

    def __init__(self, *args, **kwargs):
        classgroups = kwargs.pop("classgroups", None)
        super().__init__(*args, **kwargs)
        if classgroups is not None:
            self.fields["class_group"].queryset = classgroups


# ---------- Disciplinary Action Form ----------
class DisciplinaryActionForm(forms.ModelForm):
    class Meta:
        model = DisciplinaryAction
        fields = ["action", "date", "description"]
        widgets = {
            "action": forms.TextInput(
                attrs={
                    "placeholder": "Type of action (e.g. Late, Skipped Class, Cheating)",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe the incident or disciplinary reason in detail.",
                }
            ),
        }
        labels = {
            "action": "Action Taken",
            "date": "Date of Incident",
            "description": "Description / Notes",
        }


# ---------- Student Achievement Form ----------
from django import forms
from core.models import StudentAchievement


class StudentAchievementForm(forms.ModelForm):
    class Meta:
        model = StudentAchievement
        fields = ["title", "date_awarded", "description"]
        widgets = {
            "date_awarded": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Describe the achievement..."}
            ),
        }


# ---------- Emergency Contact Form ----------


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["emergency_name", "emergency_relation", "emergency_phone"]
        widgets = {
            "emergency_name": forms.TextInput(
                attrs={"placeholder": "e.g. Ali bin Abu"}
            ),
            "emergency_relation": forms.TextInput(
                attrs={"placeholder": "e.g. Father / Mother / Guardian"}
            ),
            "emergency_phone": forms.TextInput(
                attrs={"placeholder": "e.g. 012-3456789"}
            ),
        }

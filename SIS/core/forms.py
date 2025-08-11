# core/forms.py
from django import forms
from .models import (
    StudentAchievement, DisciplinaryAction, Attendance, Enrollment, Student, Parent,
)
from accounts.models import CustomUser



class StudentAchievementForm(forms.ModelForm):
    class Meta:
        model = StudentAchievement
        fields = ['title', 'description', 'date_awarded']

class DisciplinaryActionForm(forms.ModelForm):
    class Meta:
        model = DisciplinaryAction
        fields = ['action', 'description', 'date']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status', 'session', 'description']
        widgets = {
            'session': forms.Select(choices=Attendance.SESSION_CHOICES),
            'status': forms.Select(choices=Attendance.STATUS_CHOICES),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add notes, e.g., left early'}),
        }

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'class_group']

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'date_of_birth',
            'address',
            'phone_number',
            'profile_picture',
            'class_group',
            'emergency_name',
            'emergency_relation',
            'emergency_phone',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'profile_picture': forms.FileInput(),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

# --- Custom User Profile Update Form ---
class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'short_name',
            'identity_card_number',
            'email',
            'phone_number',
            'address',
            'profile_picture',
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}),
            'identity_card_number': forms.TextInput(attrs={'readonly': 'readonly'}),
            'profile_picture': forms.FileInput(),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
#

class StudentExtraProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'date_of_birth',
            'class_group',
            'emergency_name',
            'emergency_relation',
            'emergency_phone',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'class_group': forms.Select(attrs={'disabled': 'disabled'}),
        }


# --- Parent/Emergency Info Form ---
# core/forms.py
from django import forms
from .models import Parent

class ParentForm(forms.ModelForm):
    roles = forms.CharField(
        required=False,
        label="Relationship(s) to Student",
        help_text="Comma-separated if more than one (e.g. 'mother, guardian')."
    )

    class Meta:
        model = Parent
        fields = [
            'full_name',
            'email',
            'profile_picture',
            'phone_number',
            'address',
            'occupation',
            'roles',
        ]
        widgets = {
            'profile_picture': forms.FileInput(),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

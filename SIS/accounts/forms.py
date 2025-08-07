from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, ReadOnlyPasswordHashField
from .models import CustomUser
from core.models import Department

# ---------- Custom User Creation Form for Admin ----------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            'email', 'identity_card_number', 'full_name', 'short_name', 'role',
            'phone_number', 'address', 'department', 'profile_picture'
        )
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email address'}),
            'identity_card_number': forms.TextInput(attrs={'placeholder': 'IC Number (e.g. 001231-14-1234)'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name (as per IC)'}),
            'short_name': forms.TextInput(attrs={'placeholder': 'Short Name (e.g. Ali)'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'placeholder': 'Address', 'rows': 2}),
            'profile_picture': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['identity_card_number'].required = True
        self.fields['full_name'].required = True
        self.fields['short_name'].required = True

# ---------- Custom User Change Form for Admin ----------
class CustomUserChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'identity_card_number', 'full_name', 'short_name', 'role',
            'phone_number', 'address', 'department', 'profile_picture', 'password',
            'is_active', 'is_staff', 'is_superuser'
        )
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}),
            'identity_card_number': forms.TextInput(attrs={'readonly': 'readonly'}),
            'profile_picture': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['identity_card_number'].required = True

# ---------- Lecturer Creation Form (for admin/portal use) ----------
class LecturerCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        required=True
    )
    date_joined = forms.DateField(
        label="Date Joined",
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label="Select Department",
        required=True,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-md'})
    )

    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'short_name', 'identity_card_number', 'email', 'password',
            'department', 'phone_number', 'address', 'profile_picture', 'date_joined'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Lecturer Email'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name (as per IC)'}),
            'short_name': forms.TextInput(attrs={'placeholder': 'Short Name (e.g. Ali)'}),
            'identity_card_number': forms.TextInput(attrs={'placeholder': 'IC Number (e.g. 001231-14-1234)'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'placeholder': 'Address', 'rows': 3}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = CustomUser.Role.LECTURER
        if commit:
            user.save()
        return user

# ---------- Student Profile Update Form ----------
class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'short_name', 'identity_card_number', 'email',
            'phone_number', 'address', 'profile_picture'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}),
            'identity_card_number': forms.TextInput(attrs={'readonly': 'readonly'}),
            'profile_picture': forms.FileInput(),
        }

# ---------- Lecturer Profile Update Form ----------
class LecturerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'short_name', 'identity_card_number', 'email',
            'phone_number', 'address', 'department', 'profile_picture'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}),
            'identity_card_number': forms.TextInput(attrs={'readonly': 'readonly'}),
            'profile_picture': forms.FileInput(),
        }

# ---------- Unified Login Form (Email or IC) ----------
class UnifiedLoginForm(forms.Form):
    identifier = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Email or Identity Card Number',
            'class': 'w-full mb-4 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
        }),
        label="Email or Identity Card Number"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'w-full mb-6 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
        }),
        label="Password"
    )

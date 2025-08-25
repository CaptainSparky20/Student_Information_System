from django import forms
from accounts.models import CustomUser
from core.models import Department, Student, Course, ClassGroup, Lecturer, ClassGroup, Subject, StudentFeePlan, StudentFeeInstallment

# ---------- LECTURER CREATION FORM ----------
class LecturerCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'Enter password'
        }),
        required=False
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'Re-enter password'
        }),
        required=False
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        empty_label="Select Department",
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
        })
    )
    date_joined = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600'}),
        required=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'short_name', 'identity_card_number', 'email', 'phone_number',
            'department', 'profile_picture', 'address', 'date_joined'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
                'placeholder': 'Full Name (as per IC)',
            }),
            'short_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
                'placeholder': 'Short Name (e.g. Ali)',
            }),
            'identity_card_number': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
                'placeholder': 'IC Number',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
                'placeholder': 'Lecturer email address',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
                'placeholder': 'Phone number',
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 bg-white/10 rounded border border-white/20 text-white',
                'accept': 'image/*',
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600',
                'placeholder': 'Address',
                'rows': 2,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password or confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password") or "password123"
        user.set_password(password)
        user.role = CustomUser.Role.LECTURER
        if commit:
            user.save()
        return user

# ---------- STUDENT UPDATE FORM ----------
class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'short_name', 'email', 'department']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input'}),
            'short_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }

# ---------- STUDENT PROFILE FORM ----------
class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['phone_number', 'address', 'date_of_birth', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

# ---------- ASSIGN LECTURERS TO CLASSGROUP FORM (ManyToMany) ----------
class AssignLecturersToClassGroupForm(forms.ModelForm):
    lecturers = forms.ModelMultipleChoiceField(
        queryset=Lecturer.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Lecturers"
    )

    class Meta:
        model = ClassGroup
        fields = ['lecturers']

# ---------- ADD/EDIT COURSE FORM ----------
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'department', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded bg-white/10 text-white border border-white/20',
                'placeholder': 'Course name',
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded bg-white/10 text-white border border-white/20',
                'placeholder': 'Course code',
            }),
            'department': forms.Select(attrs={
                'class': 'w-full p-2 rounded bg-white/10 text-white border border-white/20',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 rounded bg-white/10 text-white border border-white/20',
                'placeholder': 'Course description (optional)',
            }),
        }

# ---------- ADD/EDIT DEPARTMENT FORM ----------
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded bg-white/10 text-white border border-white/20',
                'placeholder': 'Department name',
            }),
        }

# ---------- ADD STUDENT FORM ----------
class AddStudentForm(forms.Form):
    base_input_class = (
        'w-full px-4 py-3 rounded-lg '
        'bg-white/10 backdrop-blur '
        'text-white border border-white/20 '
        'placeholder-white/70 '
        'focus:ring-2 focus:ring-blue-400 focus:outline-none transition'
)
    base_select_class = (
    'w-full px-4 py-3 rounded-lg '
    'bg-white/10 backdrop-blur '
    'text-white font-medium border border-white/20 '
    'focus:ring-2 focus:ring-blue-400 focus:outline-none transition'
)

    full_name = forms.CharField(
        max_length=100,
        label="Full Name",
        widget=forms.TextInput(attrs={
            'class': base_input_class,
            'placeholder': 'Enter full name'
        })
    )
    short_name = forms.CharField(
        max_length=64,
        label="Short Name",
        required=False,
        widget=forms.TextInput(attrs={
            'class': base_input_class,
            'placeholder': 'Enter short name (optional)'
        })
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': base_input_class,
            'placeholder': 'student@example.com'
        })
    )
    identity_card_number = forms.CharField(
        max_length=20,
        label="IC/Identity Card Number",
        widget=forms.TextInput(attrs={
            'class': base_input_class,
            'placeholder': 'e.g. 001231-14-1234'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': base_input_class,
            'placeholder': 'Set a password (leave blank for default)'
        }),
        label="Password",
        required=False
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': base_input_class,
            'placeholder': 'Re-enter password'
        }),
        label="Confirm Password",
        required=False
    )
    department = forms.ModelChoiceField(
    queryset=Department.objects.all(),
    label="Department",
    widget=forms.Select(attrs={
        'class': base_select_class
    })
)

    class_group = forms.ModelChoiceField(
        queryset=ClassGroup.objects.all(),
        label="Assign to Class Group",
        widget=forms.Select(attrs={
            'class': base_select_class
    })
)
    profile_picture = forms.ImageField(
        required=False,
        label="Profile Picture",
        widget=forms.ClearableFileInput(attrs={
            'class': base_input_class
        })
    )
    phone_number = forms.CharField(
        required=False,
        max_length=20,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': base_input_class,
            'placeholder': 'Optional'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': base_input_class,
            'placeholder': 'Optional',
            'rows': 3
        }),
        required=False,
        label="Address"
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': base_input_class
        }),
        required=False,
        label="Date of Birth"
    )
    emergency_name = forms.CharField(
        max_length=255,
        required=False,
        label="Emergency Contact Name",
        widget=forms.TextInput(attrs={'class': base_input_class})
    )
    emergency_relation = forms.CharField(
        max_length=64,
        required=False,
        label="Emergency Contact Relation",
        widget=forms.TextInput(attrs={'class': base_input_class})
    )
    emergency_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Emergency Contact Phone",
        widget=forms.TextInput(attrs={'class': base_input_class})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password or confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data




# ---------- CLASS GROUP FORM ----------
class ClassGroupForm(forms.ModelForm):
    class Meta:
        model = ClassGroup
        fields = ['name', 'course', 'department', 'year', 'classroom', 'lecturers']

# ---------- SUBJECT FORM ----------
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'course', 'description']





class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500'
        }),
        strip=False
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500'
        }),
        strip=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identity_card_number'].required = True

    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'short_name', 'identity_card_number', 'email', 'profile_picture', 'phone_number',
            'department', 'date_joined', 'address'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500'
            }),
            'short_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500'
            }),
            'identity_card_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500',
                'placeholder': 'IC Number (e.g. 001231-14-1234)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white focus:ring-2 focus:ring-blue-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500'
            }),
            'department': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white focus:ring-2 focus:ring-blue-500'
            }),
            'date_joined': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white focus:ring-2 focus:ring-blue-500'
            }),
            'address': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500'
            }),
        }

    def clean_identity_card_number(self):
        value = self.cleaned_data.get('identity_card_number')
        if CustomUser.objects.filter(identity_card_number=value).exists():
            raise forms.ValidationError("A user with this identity card number already exists.")
        return value

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user


# ---------- STUDENT FEE PLAN FORM ----------
class FeePlanCreateForm(forms.ModelForm):
    class Meta:
        model = StudentFeePlan
        fields = ["student", "description", "total_amount", "months", "start_date", "status"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }

class FeePlanCreateForStudentForm(forms.ModelForm):
    """Same as above, but 'student' is fixed and hidden."""
    class Meta:
        model = StudentFeePlan
        fields = ["description", "total_amount", "months", "start_date", "status"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }

class InstallmentUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentFeeInstallment
        fields = ["is_paid", "paid_date", "note"]
        widgets = {
            "paid_date": forms.DateInput(attrs={"type": "date"}),
        }
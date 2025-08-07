# core/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone

# ---------- Department ----------
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# ---------- Course ----------
class Course(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

# ---------- Subject ----------
class Subject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

# ---------- ClassGroup ----------
class ClassGroup(models.Model):
    name = models.CharField(max_length=32)  # e.g., CS-A, CS-B
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classgroups')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classgroups')
    year = models.PositiveIntegerField(default=timezone.now().year)
    classroom = models.CharField(max_length=64, blank=True, null=True)
    lecturers = models.ManyToManyField('Lecturer', related_name='classgroups', blank=True)

    def __str__(self):
        return f"{self.name} ({self.course.code}, {self.year})"

# ---------- Lecturer ----------
class Lecturer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='lecturers')
    subjects = models.ManyToManyField(Subject, related_name='lecturers', blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        # Full name or short name from user model
        return self.user.get_full_name() or self.user.email

# ---------- Parent/Guardian ----------
class Parent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)

    ROLE_CHOICES = [
        ("father", "Father"),
        ("mother", "Mother"),
        ("guardian", "Guardian"),
        ("grandfather", "Grandfather"),
        ("grandmother", "Grandmother"),
        ("other", "Other"),
    ]
    roles = models.CharField(max_length=128, blank=True, help_text="Comma-separated roles (e.g. 'father,guardian')")

    def get_roles_list(self):
        return [r.strip().capitalize() for r in self.roles.split(',') if r.strip()]

    def __str__(self):
        return self.user.get_full_name() or self.user.email

# ---------- Student ----------
class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True, related_name='students')
    parents = models.ManyToManyField(Parent, related_name='children', blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    latest_activity = models.DateTimeField(blank=True, null=True)

    # Emergency Contact
    emergency_name = models.CharField("Emergency Contact Name", max_length=255, blank=True)
    emergency_relation = models.CharField("Emergency Contact Relation", max_length=64, blank=True)
    emergency_phone = models.CharField("Emergency Contact Phone", max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.full_name} ({self.user.identity_card_number})"

    def full_details(self):
        return {
            'name': self.user.full_name,
            'short_name': self.user.short_name,
            'ic_number': self.user.identity_card_number,
            'email': self.user.email,
            'dob': self.date_of_birth,
            'address': self.address,
            'phone': self.phone_number,
            'profile_picture_url': self.profile_picture.url if self.profile_picture else None,
            'emergency_name': self.emergency_name,
            'emergency_relation': self.emergency_relation,
            'emergency_phone': self.emergency_phone,
        }

    def update_latest_activity(self):
        self.latest_activity = timezone.now()
        self.save(update_fields=['latest_activity'])

# ---------- Enrollment ----------
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE)
    date_enrolled = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'class_group')

    def __str__(self):
        return f"{self.student} in {self.class_group}"

# ---------- Attendance ----------
class Attendance(models.Model):
    SESSION_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    ]
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    date = models.DateField()
    session = models.CharField(max_length=10, choices=SESSION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('enrollment', 'date', 'session')

    def __str__(self):
        return f"{self.enrollment.student} - {self.enrollment.class_group} - {self.date} [{self.session}] - {self.status.capitalize()}"

# ---------- Student Achievement ----------
class StudentAchievement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date_awarded = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.student}: {self.title}"

# ---------- Disciplinary Action ----------
class DisciplinaryAction(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='disciplinary_actions')
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.student}: {self.action} on {self.date}"

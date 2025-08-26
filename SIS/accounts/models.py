from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models
from core.models import Department
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not extra_fields.get("identity_card_number"):
            raise ValueError("The Identity Card Number must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password or "password123")
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)
        # Ensure required fields for superuser
        if not extra_fields.get("identity_card_number"):
            extra_fields["identity_card_number"] = "IC-ADMIN"
        if not extra_fields.get("full_name"):
            extra_fields["full_name"] = "Admin User"
        if not extra_fields.get("short_name"):
            extra_fields["short_name"] = "Admin"
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("role") != CustomUser.Role.ADMIN:
            raise ValueError("Superuser must have role=ADMIN.")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        LECTURER = "LECTURER", "Lecturer"
        ADMIN = "ADMIN", "Admin"

    # === Identity ===
    email = models.EmailField(unique=True)
    identity_card_number = models.CharField(
        max_length=20, unique=True, verbose_name="IC/Identity Card No."
    )

    # === Name Fields ===
    full_name = models.CharField(max_length=255, verbose_name="Full Name (as per IC)")
    short_name = models.CharField(
        max_length=64,
        verbose_name="Short Name",
        blank=True,
        help_text="E.g. 'Ali', for display in tables/lists",
    )

    # === Other Info ===
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["identity_card_number", "full_name", "short_name"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.identity_card_number}) - {self.email} [{self.role}]"

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.short_name or (
            self.full_name.split(" ")[0] if self.full_name else self.email
        )

    def save(self, *args, **kwargs):
        # Auto-fill short_name if not provided
        if not self.short_name and self.full_name:
            self.short_name = self.full_name.split(" ")[0]
        super().save(*args, **kwargs)


# Proxy model for Lecturers
class LecturerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=CustomUser.Role.LECTURER)


class Lecturer(CustomUser):
    objects = LecturerManager()

    class Meta:
        proxy = True
        verbose_name = "Lecturer"
        verbose_name_plural = "Lecturers"


# Proxy model for Students
class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=CustomUser.Role.STUDENT)


class Student(CustomUser):
    objects = StudentManager()

    class Meta:
        proxy = True
        verbose_name = "Student"
        verbose_name_plural = "Students"

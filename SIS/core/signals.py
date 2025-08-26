from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from .models import Student, Lecturer
from accounts.models import CustomUser  # Adjust import if needed


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create a Student or Lecturer profile when a new user is created.
    Also ensure profile exists on user update.
    """
    if created:
        if instance.role == CustomUser.Role.STUDENT:
            Student.objects.create(user=instance)
        elif instance.role == CustomUser.Role.LECTURER:
            Lecturer.objects.create(user=instance)
        # Add other roles if needed
    else:
        if instance.role == CustomUser.Role.STUDENT:
            Student.objects.get_or_create(user=instance)
        elif instance.role == CustomUser.Role.LECTURER:
            Lecturer.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def update_latest_activity(sender, request, user, **kwargs):
    """
    Update the latest_activity timestamp for Student on user login.
    """
    try:
        student = Student.objects.get(user=user)
        student.latest_activity = timezone.now()
        student.save(update_fields=["latest_activity"])
    except Student.DoesNotExist:
        pass

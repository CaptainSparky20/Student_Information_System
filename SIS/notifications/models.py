from django.db import models

# Create your models here.
# notifications/models.py
from django.db import models
from accounts.models import CustomUser


class Notification(models.Model):
    lecturer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.lecturer.email}: {self.message[:50]}"

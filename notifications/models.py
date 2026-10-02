"""Notifications internes affichées dans l'application."""

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        OVERDUE = "overdue", "Retard"
        DUE_TODAY = "due_today", "Aujourd'hui"
        DUE_SOON = "due_soon", "Bientôt"
        INFO = "info", "Information"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    task = models.ForeignKey("tasks.Task", on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    type = models.CharField(max_length=30, choices=Type.choices, default=Type.INFO)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "notification"
        verbose_name_plural = "notifications"

    def __str__(self):
        return self.message

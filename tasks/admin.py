"""Administration des tâches."""

from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "subject", "type", "priority", "status", "due_date", "due_time", "completed_at")
    list_filter = ("status", "priority", "type", "due_date", "subject")
    search_fields = ("title", "description", "user__email", "subject__name")
    date_hierarchy = "due_date"

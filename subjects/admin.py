"""Administration des matières."""

from django.contrib import admin

from .models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "teacher", "user", "color", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "code", "teacher", "user__email")

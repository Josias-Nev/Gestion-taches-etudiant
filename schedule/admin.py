"""Administration de l'emploi du temps."""

from django.contrib import admin

from .models import ScheduleEntry


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ("day_of_week", "start_time", "end_time", "subject", "room", "teacher", "user")
    list_filter = ("day_of_week", "subject")
    search_fields = ("subject__name", "room", "teacher", "user__email")

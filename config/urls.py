"""Routes principales de Study Task."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="dashboard:index", permanent=False), name="home"),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("calendar/", RedirectView.as_view(pattern_name="tasks:calendar", permanent=False), name="calendar"),
    path("deadlines/", RedirectView.as_view(pattern_name="tasks:deadlines", permanent=False), name="deadlines"),
    path("week/", RedirectView.as_view(pattern_name="tasks:week", permanent=False), name="week"),
    path("subjects/", include("subjects.urls")),
    path("tasks/", include("tasks.urls")),
    path("schedule/", include("schedule.urls")),
    path("statistics/", include("analytics.urls")),
    path("notifications/", include("notifications.urls")),
]

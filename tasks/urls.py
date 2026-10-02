"""Routes des tâches, échéances, calendrier et semaine."""

from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.task_list, name="list"),
    path("create/", views.task_create, name="create"),
    path("deadlines/", views.deadlines_view, name="deadlines"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/day/<str:day>/", views.calendar_day_view, name="calendar_day"),
    path("week/", views.week_view, name="week"),
    path("<int:pk>/", views.task_detail, name="detail"),
    path("<int:pk>/edit/", views.task_update, name="edit"),
    path("<int:pk>/delete/", views.task_delete, name="delete"),
    path("<int:pk>/toggle-complete/", views.task_toggle_complete, name="toggle_complete"),
    path("<int:pk>/status/", views.task_update_status, name="update_status"),
]

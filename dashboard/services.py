"""Calculs du tableau de bord."""

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from notifications.services import build_task_reminders
from schedule.models import ScheduleEntry
from tasks.models import Task
from tasks.services import base_tasks_for_user, completion_rate, get_overdue_tasks, get_upcoming_tasks, get_week_bounds


def get_dashboard_context(user):
    today = timezone.localdate()
    week_start, week_end = get_week_bounds(today)
    tasks = base_tasks_for_user(user)

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status=Task.Status.COMPLETED).count()
    active_tasks = tasks.exclude(status=Task.Status.COMPLETED).count()
    urgent_tasks = tasks.filter(
        Q(priority__in=[Task.Priority.HIGH, Task.Priority.URGENT])
        | Q(due_date__lte=today + timedelta(days=2), due_date__gte=today)
    ).exclude(status=Task.Status.COMPLETED)
    overdue_tasks = get_overdue_tasks(user)
    week_tasks = tasks.filter(due_date__range=[week_start, week_end])
    week_completed = week_tasks.filter(status=Task.Status.COMPLETED).count()

    subject_load = (
        tasks.filter(due_date__range=[week_start, week_end])
        .values("subject__name", "subject__color")
        .annotate(total=Count("id"), duration=Sum("estimated_duration"))
        .order_by("subject__name")
    )

    today_schedule = ScheduleEntry.objects.filter(user=user, day_of_week=today.weekday()).select_related("subject").order_by("start_time")

    return {
        "today": today,
        "stats": {
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "urgent_tasks": urgent_tasks.count(),
            "upcoming_deadlines": get_upcoming_tasks(user, days=7).count(),
            "overdue_tasks": overdue_tasks.count(),
            "total_tasks": total_tasks,
        },
        "today_tasks": tasks.filter(due_date=today).order_by("status", "due_time", "title"),
        "upcoming_tasks": get_upcoming_tasks(user, days=7)[:6],
        "overdue_tasks": overdue_tasks[:5],
        "reminders": build_task_reminders(user)[:8],
        "week_progress": completion_rate(week_tasks.count(), week_completed),
        "subject_load": subject_load,
        "today_schedule": today_schedule,
    }

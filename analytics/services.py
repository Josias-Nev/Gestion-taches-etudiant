"""Calculs statistiques réutilisables."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from subjects.models import Subject
from tasks.models import Task
from tasks.services import completion_rate, get_week_bounds


def get_statistics_context(user):
    today = timezone.localdate()
    week_start, week_end = get_week_bounds(today)
    tasks = Task.objects.filter(user=user).select_related("subject")

    total = tasks.count()
    completed = tasks.filter(status=Task.Status.COMPLETED).count()
    in_progress = tasks.filter(status=Task.Status.IN_PROGRESS).count()
    remaining = tasks.exclude(status=Task.Status.COMPLETED).count()
    overdue = tasks.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED).count()

    subject_stats = (
        Subject.objects.filter(user=user)
        .annotate(
            total_tasks=Count("tasks", filter=Q(tasks__user=user)),
            completed_tasks=Count("tasks", filter=Q(tasks__user=user, tasks__status=Task.Status.COMPLETED)),
            remaining_tasks=Count("tasks", filter=Q(tasks__user=user) & ~Q(tasks__status=Task.Status.COMPLETED)),
            overdue_tasks=Count("tasks", filter=Q(tasks__user=user, tasks__due_date__lt=today) & ~Q(tasks__status=Task.Status.COMPLETED)),
            workload=Sum("tasks__estimated_duration", filter=Q(tasks__user=user, tasks__due_date__range=[week_start, week_end])),
        )
        .order_by("name")
    )

    evolution = []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        count = tasks.filter(completed_at__date=day).count()
        evolution.append({"date": day, "count": count})
    max_evolution = max([item["count"] for item in evolution] or [0])
    for item in evolution:
        item["percent"] = round((item["count"] / max_evolution) * 100) if max_evolution else 0

    week_tasks = tasks.filter(due_date__range=[week_start, week_end])
    week_completed = week_tasks.filter(status=Task.Status.COMPLETED).count()
    total_week_duration = week_tasks.aggregate(total=Sum("estimated_duration"))["total"] or Decimal("0")

    priority_breakdown = []
    for value, label in Task.Priority.choices:
        count = tasks.filter(priority=value).count()
        priority_breakdown.append({"value": value, "label": label, "count": count})

    return {
        "stats": {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "remaining": remaining,
            "overdue": overdue,
            "completion_rate": completion_rate(total, completed),
            "week_progress": completion_rate(week_tasks.count(), week_completed),
            "week_workload": total_week_duration,
        },
        "subject_stats": subject_stats,
        "evolution": evolution,
        "priority_breakdown": priority_breakdown,
        "today": today,
    }

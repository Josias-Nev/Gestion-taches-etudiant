"""Services métier et requêtes des tâches."""

from collections import OrderedDict
from datetime import timedelta

from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from .models import Task


PRIORITY_ORDER = Case(
    When(priority=Task.Priority.URGENT, then=Value(1)),
    When(priority=Task.Priority.HIGH, then=Value(2)),
    When(priority=Task.Priority.MEDIUM, then=Value(3)),
    When(priority=Task.Priority.LOW, then=Value(4)),
    default=Value(5),
    output_field=IntegerField(),
)

STATUS_ORDER = Case(
    When(status=Task.Status.TODO, then=Value(1)),
    When(status=Task.Status.IN_PROGRESS, then=Value(2)),
    When(status=Task.Status.COMPLETED, then=Value(3)),
    default=Value(4),
    output_field=IntegerField(),
)


def base_tasks_for_user(user):
    return Task.objects.filter(user=user).select_related("subject")


def apply_task_filters(queryset, cleaned_data):
    """Applique recherche, filtres et tri combinables."""

    query = cleaned_data.get("q")
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(subject__name__icontains=query)
            | Q(subject__code__icontains=query)
        )

    subject = cleaned_data.get("subject")
    if subject:
        queryset = queryset.filter(subject=subject)

    status = cleaned_data.get("status")
    if status:
        queryset = queryset.filter(status=status)

    priority = cleaned_data.get("priority")
    if priority:
        queryset = queryset.filter(priority=priority)

    task_type = cleaned_data.get("type")
    if task_type:
        queryset = queryset.filter(type=task_type)

    today = timezone.localdate()
    period = cleaned_data.get("period")
    if period == "today":
        queryset = queryset.filter(due_date=today)
    elif period == "week":
        week_start = today - timedelta(days=today.weekday())
        queryset = queryset.filter(due_date__range=[week_start, week_start + timedelta(days=6)])
    elif period == "month":
        queryset = queryset.filter(due_date__year=today.year, due_date__month=today.month)
    elif period == "overdue":
        queryset = queryset.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED)
    elif period == "custom":
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end:
            queryset = queryset.filter(due_date__range=[start, end])

    sort = cleaned_data.get("sort") or "due"
    due_null_order = Case(
        When(due_date__isnull=True, then=Value(1)),
        default=Value(0),
        output_field=IntegerField(),
    )
    if sort == "priority":
        queryset = queryset.annotate(priority_order=PRIORITY_ORDER, due_null=due_null_order).order_by(
            "priority_order", "due_null", "due_date", "due_time", "title"
        )
    elif sort == "created":
        queryset = queryset.order_by("-created_at")
    elif sort == "subject":
        queryset = queryset.order_by("subject__name", "due_date", "due_time", "title")
    elif sort == "status":
        queryset = queryset.annotate(status_order=STATUS_ORDER).order_by("status_order", "due_date", "due_time", "title")
    else:
        queryset = queryset.annotate(due_null=due_null_order, priority_order=PRIORITY_ORDER).order_by(
            "due_null", "due_date", "due_time", "priority_order", "title"
        )
    return queryset


def group_tasks_by_status(tasks):
    grouped = OrderedDict((status, {"value": status, "label": label, "tasks": []}) for status, label in Task.Status.choices)
    for task in tasks:
        grouped.setdefault(task.status, {"value": task.status, "label": task.get_status_display(), "tasks": []})["tasks"].append(task)
    return list(grouped.values())


def get_today_tasks(user):
    today = timezone.localdate()
    return base_tasks_for_user(user).filter(due_date=today).order_by("status", "due_time", "-priority", "title")


def get_overdue_tasks(user):
    today = timezone.localdate()
    return base_tasks_for_user(user).filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED).order_by("due_date", "due_time")


def get_upcoming_tasks(user, days=7):
    today = timezone.localdate()
    return (
        base_tasks_for_user(user)
        .filter(due_date__gte=today, due_date__lte=today + timedelta(days=days))
        .exclude(status=Task.Status.COMPLETED)
        .order_by("due_date", "due_time")
    )


def get_week_bounds(reference_date=None):
    reference_date = reference_date or timezone.localdate()
    week_start = reference_date - timedelta(days=reference_date.weekday())
    return week_start, week_start + timedelta(days=6)


def completion_rate(total, completed):
    if total == 0:
        return 0
    return round((completed / total) * 100)

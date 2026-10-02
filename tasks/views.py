"""Vues des tâches, du calendrier, des échéances et de la semaine."""

import calendar as calendar_module
from collections import OrderedDict
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from schedule.models import ScheduleEntry
from subjects.models import Subject

from .forms import TaskFilterForm, TaskForm, TaskStatusForm
from .models import Task
from .services import (
    apply_task_filters,
    base_tasks_for_user,
    completion_rate,
    get_overdue_tasks,
    get_upcoming_tasks,
    get_week_bounds,
    group_tasks_by_status,
)


def _redirect_back(request, fallback="tasks:list"):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(fallback)


@login_required
def task_list(request):
    filter_form = TaskFilterForm(request.GET or None, user=request.user)
    tasks = base_tasks_for_user(request.user)
    if filter_form.is_valid():
        tasks = apply_task_filters(tasks, filter_form.cleaned_data)
        current_view = filter_form.cleaned_data.get("view") or "list"
    else:
        tasks = tasks.order_by("due_date", "due_time", "title")
        current_view = request.GET.get("view", "list")

    grouped = group_tasks_by_status(tasks) if current_view == "kanban" else None
    context = {
        "filter_form": filter_form,
        "tasks": tasks,
        "grouped_tasks": grouped,
        "current_view": current_view,
        "status_form": TaskStatusForm(),
        "status_choices": Task.Status.choices,
        "today": timezone.localdate(),
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def task_create(request):
    initial = {}
    subject_id = request.GET.get("subject")
    if subject_id and Subject.objects.filter(pk=subject_id, user=request.user).exists():
        initial["subject"] = subject_id
    form = TaskForm(request.POST or None, user=request.user, initial=initial)
    if request.method == "POST" and form.is_valid():
        task = form.save()
        messages.success(request, "Tâche créée avec succès.")
        return redirect("tasks:detail", pk=task.pk)
    return render(request, "tasks/task_form.html", {"form": form, "title": "Nouvelle tâche"})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(base_tasks_for_user(request.user), pk=pk)
    return render(request, "tasks/task_detail.html", {"task": task, "today": timezone.localdate()})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    form = TaskForm(request.POST or None, instance=task, user=request.user)
    if request.method == "POST" and form.is_valid():
        task = form.save()
        messages.success(request, "Tâche modifiée avec succès.")
        return redirect("tasks:detail", pk=task.pk)
    return render(request, "tasks/task_form.html", {"form": form, "title": "Modifier la tâche", "task": task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Tâche supprimée avec succès.")
        return redirect("tasks:list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
@require_POST
def task_toggle_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == Task.Status.COMPLETED:
        task.reopen(Task.Status.IN_PROGRESS)
        messages.success(request, "La tâche a été remise en cours.")
    else:
        task.mark_completed()
        messages.success(request, "Tâche marquée comme terminée.")
    return _redirect_back(request)


@login_required
@require_POST
def task_update_status(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    form = TaskStatusForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, "Statut mis à jour.")
    else:
        messages.error(request, "Impossible de modifier le statut de cette tâche.")
    return _redirect_back(request)


@login_required
def deadlines_view(request):
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    week_start, week_end = get_week_bounds(today)

    tasks = base_tasks_for_user(request.user)
    overdue_tasks = list(get_overdue_tasks(request.user))
    overdue_items = [{"task": task, "days_late": (today - task.due_date).days} for task in overdue_tasks]
    context = {
        "today_tasks": tasks.filter(due_date=today).order_by("due_time", "title"),
        "tomorrow_tasks": tasks.filter(due_date=tomorrow).exclude(status=Task.Status.COMPLETED).order_by("due_time", "title"),
        "week_tasks": tasks.filter(due_date__range=[week_start, week_end]).exclude(status=Task.Status.COMPLETED).order_by("due_date", "due_time"),
        "overdue_tasks": overdue_tasks,
        "overdue_items": overdue_items,
        "today": today,
    }
    return render(request, "tasks/deadlines.html", context)


@login_required
def calendar_view(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        current = date(year, month, 1)
    except (TypeError, ValueError):
        current = today.replace(day=1)

    previous_month = current.replace(day=1) - timedelta(days=1)
    if current.month == 12:
        next_month = current.replace(year=current.year + 1, month=1, day=1)
    else:
        next_month = current.replace(month=current.month + 1, day=1)

    month_tasks = list(
        base_tasks_for_user(request.user)
        .filter(due_date__year=current.year, due_date__month=current.month)
        .order_by("due_date", "due_time", "title")
    )
    tasks_by_day = {}
    for task in month_tasks:
        tasks_by_day.setdefault(task.due_date.day, []).append(task)

    month_matrix = calendar_module.Calendar(firstweekday=0).monthdatescalendar(current.year, current.month)
    weeks = []
    for week in month_matrix:
        days = []
        for day in week:
            day_tasks = tasks_by_day.get(day.day, []) if day.month == current.month else []
            days.append(
                {
                    "date": day,
                    "in_month": day.month == current.month,
                    "is_today": day == today,
                    "tasks": day_tasks,
                    "url": reverse("tasks:calendar_day", kwargs={"day": day.isoformat()}),
                }
            )
        weeks.append(days)

    context = {
        "current": current,
        "weeks": weeks,
        "previous_month": previous_month,
        "next_month": next_month,
        "today": today,
    }
    return render(request, "tasks/calendar.html", context)


@login_required
def calendar_day_view(request, day):
    try:
        selected_date = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Date invalide.")
        return redirect("tasks:calendar")

    tasks = base_tasks_for_user(request.user).filter(due_date=selected_date).order_by("due_time", "title")
    return render(request, "tasks/calendar_day.html", {"selected_date": selected_date, "tasks": tasks, "today": timezone.localdate()})


@login_required
def week_view(request):
    today = timezone.localdate()
    try:
        reference_date = datetime.strptime(request.GET.get("date", today.isoformat()), "%Y-%m-%d").date()
    except ValueError:
        reference_date = today

    week_start, week_end = get_week_bounds(reference_date)
    previous_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    week_tasks = list(
        base_tasks_for_user(request.user)
        .filter(due_date__range=[week_start, week_end])
        .order_by("due_date", "due_time", "title")
    )
    entries = ScheduleEntry.objects.filter(user=request.user).select_related("subject").order_by("day_of_week", "start_time")

    days = OrderedDict()
    french_days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    for index in range(7):
        current_date = week_start + timedelta(days=index)
        day_tasks = [task for task in week_tasks if task.due_date == current_date]
        day_entries = [entry for entry in entries if entry.day_of_week == index]
        days[current_date] = {
            "name": french_days[index],
            "tasks": day_tasks,
            "entries": day_entries,
            "total_duration": sum((task.estimated_duration or Decimal("0")) for task in day_tasks),
        }

    workload_by_subject = []
    subjects = Subject.objects.filter(user=request.user).order_by("name")
    for subject in subjects:
        total = (
            Task.objects.filter(user=request.user, subject=subject, due_date__range=[week_start, week_end])
            .aggregate(total=Sum("estimated_duration"))["total"]
            or Decimal("0")
        )
        if total:
            workload_by_subject.append({"subject": subject, "hours": total})
    unassigned_total = (
        Task.objects.filter(user=request.user, subject__isnull=True, due_date__range=[week_start, week_end]).aggregate(total=Sum("estimated_duration"))["total"]
        or Decimal("0")
    )

    total_week_tasks = len(week_tasks)
    completed_week_tasks = len([task for task in week_tasks if task.status == Task.Status.COMPLETED])
    total_duration = sum((task.estimated_duration or Decimal("0")) for task in week_tasks)

    context = {
        "days": days,
        "week_start": week_start,
        "week_end": week_end,
        "previous_week": previous_week,
        "next_week": next_week,
        "workload_by_subject": workload_by_subject,
        "unassigned_total": unassigned_total,
        "total_duration": total_duration,
        "progress_rate": completion_rate(total_week_tasks, completed_week_tasks),
        "today": today,
    }
    return render(request, "tasks/week.html", context)

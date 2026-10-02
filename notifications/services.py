"""Génération de rappels internes à partir des vraies données."""

from datetime import timedelta

from django.utils import timezone

from tasks.models import Task
from tasks.services import base_tasks_for_user


def build_task_reminders(user):
    """Retourne des rappels non persistants calculés depuis les tâches de l'étudiant."""

    today = timezone.localdate()
    tasks = base_tasks_for_user(user).exclude(status=Task.Status.COMPLETED)
    overdue_count = tasks.filter(due_date__lt=today).count()
    reminders = []

    if overdue_count:
        reminders.append(
            {
                "type": "danger",
                "title": "Tâches en retard",
                "message": f"Vous avez {overdue_count} tâche{'s' if overdue_count > 1 else ''} en retard.",
                "url_name": "tasks:deadlines",
            }
        )

    for task in tasks.filter(due_date=today).order_by("due_time", "title")[:5]:
        reminders.append(
            {
                "type": "warning",
                "title": "Échéance aujourd'hui",
                "message": f"{task.title} doit être terminé aujourd'hui.",
                "task": task,
            }
        )

    tomorrow = today + timedelta(days=1)
    for task in tasks.filter(due_date=tomorrow).order_by("due_time", "title")[:5]:
        reminders.append(
            {
                "type": "info",
                "title": "Échéance demain",
                "message": f"{task.title} arrive à échéance demain.",
                "task": task,
            }
        )

    soon_end = today + timedelta(days=3)
    for task in tasks.filter(due_date__gt=tomorrow, due_date__lte=soon_end).order_by("due_date", "due_time")[:5]:
        delta = (task.due_date - today).days
        reminders.append(
            {
                "type": "neutral",
                "title": "Échéance proche",
                "message": f"{task.title} arrive à échéance dans {delta} jours.",
                "task": task,
            }
        )

    return reminders

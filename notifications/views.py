"""Vues des notifications internes."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification
from .services import build_task_reminders


@login_required
def notification_list(request):
    stored_notifications = Notification.objects.filter(user=request.user).select_related("task")
    reminders = build_task_reminders(request.user)
    return render(
        request,
        "notifications/notification_list.html",
        {"stored_notifications": stored_notifications, "reminders": reminders},
    )


@login_required
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    messages.success(request, "Notification marquée comme lue.")
    return redirect("notifications:list")

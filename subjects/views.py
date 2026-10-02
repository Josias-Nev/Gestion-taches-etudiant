"""Vues de gestion des matières."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import SubjectForm
from .models import Subject


@login_required
def subject_list(request):
    subjects = (
        Subject.objects.filter(user=request.user)
        .annotate(
            total_tasks=Count("tasks", filter=Q(tasks__user=request.user)),
            completed_tasks=Count("tasks", filter=Q(tasks__user=request.user, tasks__status="completed")),
        )
        .order_by("name")
    )
    return render(request, "subjects/subject_list.html", {"subjects": subjects})


@login_required
def subject_create(request):
    form = SubjectForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        subject = form.save()
        messages.success(request, "Matière créée avec succès.")
        return redirect("subjects:detail", pk=subject.pk)
    return render(request, "subjects/subject_form.html", {"form": form, "title": "Nouvelle matière"})


@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    tasks = subject.tasks.filter(user=request.user).select_related("subject").order_by("due_date", "due_time", "title")
    today = timezone.localdate()
    stats = {
        "total": tasks.count(),
        "completed": tasks.filter(status="completed").count(),
        "remaining": tasks.exclude(status="completed").count(),
        "overdue": tasks.filter(due_date__lt=today).exclude(status="completed").count(),
    }
    return render(request, "subjects/subject_detail.html", {"subject": subject, "tasks": tasks, "stats": stats})


@login_required
def subject_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    form = SubjectForm(request.POST or None, instance=subject, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Matière modifiée avec succès.")
        return redirect("subjects:detail", pk=subject.pk)
    return render(request, "subjects/subject_form.html", {"form": form, "title": "Modifier la matière", "subject": subject})


@login_required
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    if request.method == "POST":
        subject.delete()
        messages.success(request, "Matière supprimée. Les tâches associées restent accessibles sans matière.")
        return redirect("subjects:list")
    return render(request, "subjects/subject_confirm_delete.html", {"subject": subject})

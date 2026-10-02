"""Vues de l'emploi du temps."""

from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ScheduleEntryForm
from .models import ScheduleEntry


@login_required
def schedule_list(request):
    entries = ScheduleEntry.objects.filter(user=request.user).select_related("subject").order_by("day_of_week", "start_time")
    days = OrderedDict((value, {"label": label, "entries": []}) for value, label in ScheduleEntry.Day.choices)
    for entry in entries:
        days[entry.day_of_week]["entries"].append(entry)
    return render(request, "schedule/schedule_list.html", {"days": days})


@login_required
def schedule_create(request):
    form = ScheduleEntryForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Créneau ajouté à l'emploi du temps.")
        return redirect("schedule:list")
    return render(request, "schedule/schedule_form.html", {"form": form, "title": "Ajouter un créneau"})


@login_required
def schedule_update(request, pk):
    entry = get_object_or_404(ScheduleEntry, pk=pk, user=request.user)
    form = ScheduleEntryForm(request.POST or None, instance=entry, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Créneau modifié.")
        return redirect("schedule:list")
    return render(request, "schedule/schedule_form.html", {"form": form, "title": "Modifier le créneau", "entry": entry})


@login_required
def schedule_delete(request, pk):
    entry = get_object_or_404(ScheduleEntry, pk=pk, user=request.user)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Créneau supprimé.")
        return redirect("schedule:list")
    return render(request, "schedule/schedule_confirm_delete.html", {"entry": entry})

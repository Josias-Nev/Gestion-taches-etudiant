"""Tableau de bord étudiant."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_dashboard_context


@login_required
def index(request):
    return render(request, "dashboard/index.html", get_dashboard_context(request.user))

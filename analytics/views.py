"""Vues statistiques."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_statistics_context


@login_required
def statistics_view(request):
    return render(request, "analytics/statistics.html", get_statistics_context(request.user))

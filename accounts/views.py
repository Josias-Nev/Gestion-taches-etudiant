"""Vues d'authentification et de profil."""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import EmailAuthenticationForm, ProfileForm, StudentRegistrationForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Votre compte a été créé avec succès. Bienvenue !")
        return redirect("dashboard:index")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Connexion réussie.")
        next_url = request.GET.get("next")
        return redirect(next_url or "dashboard:index")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Vous êtes déconnecté.")
        return redirect("accounts:login")
    return render(request, "accounts/logout_confirm.html")


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})

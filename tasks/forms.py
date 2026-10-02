"""Formulaires des tâches avec validation serveur."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from subjects.models import Subject

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "subject",
            "type",
            "priority",
            "status",
            "due_date",
            "due_time",
            "estimated_duration",
        ]
        labels = {
            "title": "Titre",
            "description": "Description",
            "subject": "Matière",
            "type": "Type",
            "priority": "Priorité",
            "status": "Statut",
            "due_date": "Date d'échéance",
            "due_time": "Heure d'échéance",
            "estimated_duration": "Durée estimée (heures)",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex. Terminer le TP SQL"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Détails, consignes, liens utiles..."}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "due_time": forms.TimeInput(attrs={"type": "time"}),
            "estimated_duration": forms.NumberInput(attrs={"min": "0", "step": "0.25", "placeholder": "Ex. 2"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(user=self.user).order_by("name")
        self.fields["subject"].required = False
        self.fields["subject"].empty_label = "Sans matière"
        self.fields["due_date"].required = False
        self.fields["due_time"].required = False
        self.fields["estimated_duration"].required = False

        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError("Le titre est obligatoire.")
        return title

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        # DateField de Django valide déjà le format. Ce point garde un message métier explicite.
        return due_date

    def clean_due_time(self):
        due_time = self.cleaned_data.get("due_time")
        return due_time

    def clean_estimated_duration(self):
        duration = self.cleaned_data.get("estimated_duration")
        if duration is not None and duration < 0:
            raise ValidationError("La durée estimée ne peut pas être négative.")
        return duration

    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get("subject")
        due_time = cleaned_data.get("due_time")
        due_date = cleaned_data.get("due_date")
        if subject and subject.user_id != self.user.id:
            self.add_error("subject", "Cette matière ne vous appartient pas.")
        if due_time and not due_date:
            self.add_error("due_date", "Sélectionnez une date si vous indiquez une heure d'échéance.")
        return cleaned_data

    def save(self, commit=True):
        task = super().save(commit=False)
        if self.user is not None:
            task.user = self.user
        if commit:
            task.save()
        return task


class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-control compact-control"})}


class TaskFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Recherche", widget=forms.TextInput(attrs={"placeholder": "Rechercher une tâche..."}))
    subject = forms.ModelChoiceField(required=False, queryset=Subject.objects.none(), empty_label="Toutes les matières")
    status = forms.ChoiceField(required=False, choices=[("", "Tous les statuts")] + list(Task.Status.choices))
    priority = forms.ChoiceField(required=False, choices=[("", "Toutes les priorités")] + list(Task.Priority.choices))
    type = forms.ChoiceField(required=False, choices=[("", "Tous les types")] + list(Task.Type.choices))
    period = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Toutes les périodes"),
            ("today", "Aujourd'hui"),
            ("week", "Cette semaine"),
            ("month", "Ce mois"),
            ("overdue", "En retard"),
            ("custom", "Personnalisée"),
        ],
    )
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("due", "Échéance la plus proche"),
            ("priority", "Priorité"),
            ("created", "Date de création"),
            ("subject", "Matière"),
            ("status", "Statut"),
        ],
    )
    view = forms.ChoiceField(required=False, choices=[("list", "Liste"), ("kanban", "Kanban")])

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(user=user).order_by("name")
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("period") == "custom":
            start = cleaned_data.get("start_date")
            end = cleaned_data.get("end_date")
            if not start or not end:
                raise ValidationError("Indiquez une date de début et une date de fin pour la période personnalisée.")
            if start > end:
                raise ValidationError("La date de début doit être antérieure à la date de fin.")
        return cleaned_data

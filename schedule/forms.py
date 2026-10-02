"""Formulaires de l'emploi du temps."""

from django import forms
from django.core.exceptions import ValidationError

from subjects.models import Subject

from .models import ScheduleEntry


class ScheduleEntryForm(forms.ModelForm):
    class Meta:
        model = ScheduleEntry
        fields = ["subject", "day_of_week", "start_time", "end_time", "room", "teacher"]
        labels = {
            "subject": "Matière",
            "day_of_week": "Jour",
            "start_time": "Heure de début",
            "end_time": "Heure de fin",
            "room": "Salle",
            "teacher": "Enseignant",
        }
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "room": forms.TextInput(attrs={"placeholder": "Ex. Salle B12"}),
            "teacher": forms.TextInput(attrs={"placeholder": "Ex. M. Dupont"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(user=self.user).order_by("name")
        self.fields["subject"].empty_label = "Sans matière"
        self.fields["subject"].required = False
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        subject = cleaned_data.get("subject")
        if start and end and start >= end:
            self.add_error("end_time", "L'heure de fin doit être après l'heure de début.")
        if subject and subject.user_id != self.user.id:
            self.add_error("subject", "Cette matière ne vous appartient pas.")
        return cleaned_data

    def save(self, commit=True):
        entry = super().save(commit=False)
        if self.user is not None:
            entry.user = self.user
        if commit:
            entry.save()
        return entry

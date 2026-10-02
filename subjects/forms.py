"""Formulaire de création et modification des matières."""

from django import forms
from django.core.exceptions import ValidationError

from .models import Subject


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "teacher", "description", "color"]
        labels = {
            "name": "Nom de la matière",
            "code": "Code",
            "teacher": "Enseignant",
            "description": "Description",
            "color": "Couleur",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex. Base de données"}),
            "code": forms.TextInput(attrs={"placeholder": "Ex. BD203"}),
            "teacher": forms.TextInput(attrs={"placeholder": "Ex. M. Dupont"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Notes sur la matière..."}),
            "color": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-control color-input" if name == "color" else "form-control"
            field.widget.attrs["class"] = css

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Le nom de la matière est obligatoire.")
        queryset = Subject.objects.filter(user=self.user, name__iexact=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError("Vous avez déjà une matière avec ce nom.")
        return name

    def save(self, commit=True):
        subject = super().save(commit=False)
        if self.user is not None:
            subject.user = self.user
        if commit:
            subject.save()
        return subject

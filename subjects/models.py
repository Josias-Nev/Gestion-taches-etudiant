"""Matières académiques créées par chaque étudiant."""

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class Subject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField("nom", max_length=120)
    code = models.CharField("code", max_length=40, blank=True)
    teacher = models.CharField("enseignant", max_length=120, blank=True)
    description = models.TextField("description", blank=True)
    color = models.CharField(
        "couleur",
        max_length=7,
        default="#2563eb",
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Utilisez une couleur hexadécimale valide, ex. #2563eb.")],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_subject_name_per_user"),
        ]
        verbose_name = "matière"
        verbose_name_plural = "matières"

    def __str__(self):
        return self.name

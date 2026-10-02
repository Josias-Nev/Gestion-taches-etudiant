"""Modèles liés aux tâches académiques."""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class Type(models.TextChoices):
        HOMEWORK = "homework", "Devoir"
        PRACTICAL_WORK = "practical_work", "TP"
        PROJECT = "project", "Projet"
        REVISION = "revision", "Révision"
        READING = "reading", "Lecture"
        EXERCISE = "exercise", "Exercice"
        EXAM = "exam", "Examen"
        PRESENTATION = "presentation", "Présentation"
        OTHER = "other", "Autre"

    class Priority(models.TextChoices):
        LOW = "low", "Basse"
        MEDIUM = "medium", "Moyenne"
        HIGH = "high", "Haute"
        URGENT = "urgent", "Urgente"

    class Status(models.TextChoices):
        TODO = "todo", "À faire"
        IN_PROGRESS = "in_progress", "En cours"
        COMPLETED = "completed", "Terminée"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    subject = models.ForeignKey(
        "subjects.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="matière",
    )
    title = models.CharField("titre", max_length=180)
    description = models.TextField("description", blank=True)
    type = models.CharField("type", max_length=30, choices=Type.choices, default=Type.HOMEWORK)
    priority = models.CharField("priorité", max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField("statut", max_length=20, choices=Status.choices, default=Status.TODO)
    due_date = models.DateField("date d'échéance", null=True, blank=True)
    due_time = models.TimeField("heure d'échéance", null=True, blank=True)
    estimated_duration = models.DecimalField(
        "durée estimée (heures)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Durée informative en heures, ex. 2.5 pour 2h30.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "due_date", "due_time", "-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "due_date"]),
            models.Index(fields=["user", "priority"]),
        ]
        verbose_name = "tâche"
        verbose_name_plural = "tâches"

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if not self.title or not self.title.strip():
            raise ValidationError({"title": "Le titre est obligatoire."})
        if self.subject_id and self.user_id and self.subject.user_id != self.user_id:
            raise ValidationError({"subject": "Cette matière n'appartient pas à l'utilisateur connecté."})

    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.strip()
        if self.status == self.Status.COMPLETED:
            if self.completed_at is None:
                self.completed_at = timezone.now()
        else:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def is_overdue(self):
        return bool(self.due_date and self.due_date < timezone.localdate() and not self.is_completed)

    @property
    def is_due_today(self):
        return self.due_date == timezone.localdate()

    @property
    def is_urgent(self):
        today = timezone.localdate()
        return self.priority in {self.Priority.HIGH, self.Priority.URGENT} or bool(
            self.due_date and self.due_date <= today + timedelta(days=2) and not self.is_completed
        )

    @property
    def priority_rank(self):
        return {
            self.Priority.URGENT: 4,
            self.Priority.HIGH: 3,
            self.Priority.MEDIUM: 2,
            self.Priority.LOW: 1,
        }.get(self.priority, 0)

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.save(update_fields=["status", "completed_at", "updated_at"])

    def reopen(self, status=None):
        self.status = status or self.Status.IN_PROGRESS
        self.completed_at = None
        self.save(update_fields=["status", "completed_at", "updated_at"])

"""Entrées de l'emploi du temps hebdomadaire."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ScheduleEntry(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 0, "Lundi"
        TUESDAY = 1, "Mardi"
        WEDNESDAY = 2, "Mercredi"
        THURSDAY = 3, "Jeudi"
        FRIDAY = 4, "Vendredi"
        SATURDAY = 5, "Samedi"
        SUNDAY = 6, "Dimanche"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="schedule_entries")
    subject = models.ForeignKey(
        "subjects.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedule_entries",
        verbose_name="matière",
    )
    day_of_week = models.PositiveSmallIntegerField("jour", choices=Day.choices)
    start_time = models.TimeField("heure de début")
    end_time = models.TimeField("heure de fin")
    room = models.CharField("salle", max_length=80, blank=True)
    teacher = models.CharField("enseignant", max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]
        verbose_name = "créneau"
        verbose_name_plural = "créneaux"

    def __str__(self):
        subject = self.subject.name if self.subject else "Cours"
        return f"{self.get_day_of_week_display()} {self.start_time:%H:%M} — {subject}"

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "L'heure de fin doit être après l'heure de début."})
        if self.subject_id and self.user_id and self.subject.user_id != self.user_id:
            raise ValidationError({"subject": "Cette matière ne vous appartient pas."})

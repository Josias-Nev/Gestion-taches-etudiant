"""Commande de développement pour générer des données de démonstration."""

from datetime import timedelta, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from schedule.models import ScheduleEntry
from subjects.models import Subject
from tasks.models import Task


class Command(BaseCommand):
    help = "Crée un compte demo@example.com avec matières, tâches et emploi du temps de démonstration."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Supprime les données de démonstration avant recréation.")

    def handle(self, *args, **options):
        User = get_user_model()
        email = "demo@example.com"
        if options["reset"]:
            User.objects.filter(email=email).delete()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"name": "Étudiant Démo", "is_active": True},
        )
        if created:
            user.set_password("DemoPass123!")
            user.save(update_fields=["password"])

        colors = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#dc2626"]
        subject_specs = [
            ("Base de données", "BD203", "M. Dupont"),
            ("Algorithmique", "ALG101", "Mme Kora"),
            ("Merise", "MER210", "M. Houssou"),
            ("Réseaux", "RES305", "Mme Sossa"),
            ("Mathématiques", "MAT120", "Dr Mensah"),
        ]
        subjects = []
        for index, (name, code, teacher) in enumerate(subject_specs):
            subject, _ = Subject.objects.get_or_create(
                user=user,
                name=name,
                defaults={"code": code, "teacher": teacher, "color": colors[index]},
            )
            subjects.append(subject)

        today = timezone.localdate()
        task_specs = [
            ("Réviser SQL", subjects[0], Task.Type.REVISION, Task.Priority.HIGH, Task.Status.TODO, today, time(18, 0), Decimal("1.50")),
            ("Terminer le TP de Merise", subjects[2], Task.Type.PRACTICAL_WORK, Task.Priority.MEDIUM, Task.Status.IN_PROGRESS, today, time(22, 0), Decimal("2.00")),
            ("Lire le chapitre 3", subjects[1], Task.Type.READING, Task.Priority.LOW, Task.Status.COMPLETED, today, None, Decimal("1.00")),
            ("Projet Web", subjects[0], Task.Type.PROJECT, Task.Priority.URGENT, Task.Status.IN_PROGRESS, today + timedelta(days=1), time(23, 59), Decimal("4.00")),
            ("Exercices de graphes", subjects[1], Task.Type.EXERCISE, Task.Priority.MEDIUM, Task.Status.TODO, today + timedelta(days=2), None, Decimal("2.50")),
            ("Préparer présentation réseaux", subjects[3], Task.Type.PRESENTATION, Task.Priority.HIGH, Task.Status.TODO, today + timedelta(days=3), time(10, 0), Decimal("3.00")),
            ("Révisions examen maths", subjects[4], Task.Type.EXAM, Task.Priority.URGENT, Task.Status.TODO, today + timedelta(days=5), None, Decimal("5.00")),
            ("TP Réseaux", subjects[3], Task.Type.PRACTICAL_WORK, Task.Priority.HIGH, Task.Status.TODO, today - timedelta(days=2), time(20, 0), Decimal("2.00")),
            ("Compte rendu Merise", subjects[2], Task.Type.HOMEWORK, Task.Priority.MEDIUM, Task.Status.TODO, today - timedelta(days=1), None, Decimal("1.50")),
            ("Fiche de synthèse SQL", subjects[0], Task.Type.REVISION, Task.Priority.LOW, Task.Status.COMPLETED, today - timedelta(days=3), None, Decimal("1.00")),
            ("Mini projet algorithmique", subjects[1], Task.Type.PROJECT, Task.Priority.HIGH, Task.Status.IN_PROGRESS, today + timedelta(days=8), None, Decimal("6.00")),
            ("Lecture routage IP", subjects[3], Task.Type.READING, Task.Priority.LOW, Task.Status.TODO, today + timedelta(days=4), None, Decimal("1.00")),
            ("Devoir matrices", subjects[4], Task.Type.HOMEWORK, Task.Priority.MEDIUM, Task.Status.TODO, today + timedelta(days=6), time(17, 0), Decimal("2.00")),
            ("Réviser normalisation", subjects[0], Task.Type.REVISION, Task.Priority.MEDIUM, Task.Status.COMPLETED, today - timedelta(days=4), None, Decimal("1.50")),
            ("Exercice jointures", subjects[0], Task.Type.EXERCISE, Task.Priority.MEDIUM, Task.Status.TODO, today + timedelta(days=9), None, Decimal("1.25")),
        ]
        for title, subject, task_type, priority, status, due_date, due_time, duration in task_specs:
            task, _ = Task.objects.update_or_create(
                user=user,
                title=title,
                defaults={
                    "subject": subject,
                    "type": task_type,
                    "priority": priority,
                    "status": status,
                    "due_date": due_date,
                    "due_time": due_time,
                    "estimated_duration": duration,
                    "description": f"Donnée de démonstration pour {title}.",
                },
            )
            if status == Task.Status.COMPLETED and not task.completed_at:
                task.mark_completed()

        ScheduleEntry.objects.get_or_create(
            user=user,
            subject=subjects[0],
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(10, 0),
            defaults={"room": "Salle B12", "teacher": subjects[0].teacher},
        )
        ScheduleEntry.objects.get_or_create(
            user=user,
            subject=subjects[1],
            day_of_week=0,
            start_time=time(14, 0),
            end_time=time(16, 0),
            defaults={"room": "Salle A04", "teacher": subjects[1].teacher},
        )
        ScheduleEntry.objects.get_or_create(
            user=user,
            subject=subjects[3],
            day_of_week=2,
            start_time=time(10, 0),
            end_time=time(12, 0),
            defaults={"room": "Lab Réseaux", "teacher": subjects[3].teacher},
        )

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))
        self.stdout.write("Compte : demo@example.com / DemoPass123!")

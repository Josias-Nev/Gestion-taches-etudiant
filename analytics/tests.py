from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from subjects.models import Subject
from tasks.models import Task


class StatisticsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!", name="A")
        self.subject = Subject.objects.create(user=self.user, name="Algorithmique")
        self.client.login(username="a@example.com", password="StrongPass123!")

    def test_statistics_match_data(self):
        today = timezone.localdate()
        Task.objects.create(user=self.user, subject=self.subject, title="Terminé", status=Task.Status.COMPLETED, due_date=today)
        Task.objects.create(user=self.user, subject=self.subject, title="Cours", status=Task.Status.IN_PROGRESS, due_date=today)
        Task.objects.create(user=self.user, subject=self.subject, title="Retard", due_date=today - timedelta(days=2))

        response = self.client.get(reverse("analytics:statistics"))
        stats = response.context["stats"]
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["in_progress"], 1)
        self.assertEqual(stats["remaining"], 2)
        self.assertEqual(stats["overdue"], 1)
        self.assertEqual(stats["completion_rate"], 33)

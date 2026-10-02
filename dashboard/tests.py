from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from subjects.models import Subject
from tasks.models import Task


class DashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!", name="A")
        self.subject = Subject.objects.create(user=self.user, name="Base de données")
        self.client.login(username="a@example.com", password="StrongPass123!")

    def test_dashboard_counts_real_data(self):
        today = timezone.localdate()
        Task.objects.create(user=self.user, subject=self.subject, title="Aujourd'hui", due_date=today, priority=Task.Priority.HIGH)
        Task.objects.create(user=self.user, subject=self.subject, title="Terminée", status=Task.Status.COMPLETED, due_date=today)
        Task.objects.create(user=self.user, subject=self.subject, title="Retard", due_date=today - timedelta(days=1))

        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.context["stats"]["active_tasks"], 2)
        self.assertEqual(response.context["stats"]["completed_tasks"], 1)
        self.assertEqual(response.context["stats"]["overdue_tasks"], 1)
        self.assertContains(response, "Aujourd&#x27;hui")
        self.assertContains(response, "Retard")

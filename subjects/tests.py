from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tasks.models import Task

from .models import Subject


class SubjectTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!", name="A")
        self.other = User.objects.create_user(email="b@example.com", password="StrongPass123!", name="B")
        self.client.login(username="a@example.com", password="StrongPass123!")

    def test_create_subject(self):
        response = self.client.post(
            reverse("subjects:create"),
            {"name": "Base de données", "code": "BD203", "teacher": "M. Dupont", "description": "SQL", "color": "#2563eb"},
        )
        subject = Subject.objects.get(user=self.user, name="Base de données")
        self.assertRedirects(response, reverse("subjects:detail", kwargs={"pk": subject.pk}))
        self.assertEqual(subject.code, "BD203")

    def test_update_subject(self):
        subject = Subject.objects.create(user=self.user, name="SQL", color="#2563eb")
        response = self.client.post(
            reverse("subjects:edit", kwargs={"pk": subject.pk}),
            {"name": "Base de données", "code": "BD203", "teacher": "Mme", "description": "", "color": "#16a34a"},
        )
        self.assertRedirects(response, reverse("subjects:detail", kwargs={"pk": subject.pk}))
        subject.refresh_from_db()
        self.assertEqual(subject.name, "Base de données")
        self.assertEqual(subject.color, "#16a34a")

    def test_delete_subject_keeps_tasks_without_subject(self):
        subject = Subject.objects.create(user=self.user, name="Réseaux")
        task = Task.objects.create(user=self.user, subject=subject, title="TP Réseaux")
        response = self.client.post(reverse("subjects:delete", kwargs={"pk": subject.pk}))
        self.assertRedirects(response, reverse("subjects:list"))
        task.refresh_from_db()
        self.assertIsNone(task.subject)

    def test_user_cannot_view_other_subject(self):
        other_subject = Subject.objects.create(user=self.other, name="Privé")
        response = self.client.get(reverse("subjects:detail", kwargs={"pk": other_subject.pk}))
        self.assertEqual(response.status_code, 404)

    def test_list_only_shows_current_user_subjects(self):
        Subject.objects.create(user=self.user, name="Algorithmique")
        Subject.objects.create(user=self.other, name="Mathématiques privées")
        response = self.client.get(reverse("subjects:list"))
        self.assertContains(response, "Algorithmique")
        self.assertNotContains(response, "Mathématiques privées")

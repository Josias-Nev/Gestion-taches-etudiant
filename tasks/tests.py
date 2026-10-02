from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from subjects.models import Subject

from .forms import TaskForm
from .models import Task


class TaskModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!", name="A")
        self.other = User.objects.create_user(email="b@example.com", password="StrongPass123!", name="B")
        self.subject = Subject.objects.create(user=self.user, name="Base de données")
        self.other_subject = Subject.objects.create(user=self.other, name="Privé")

    def test_completed_at_is_set_and_cleared(self):
        task = Task.objects.create(user=self.user, subject=self.subject, title="TP SQL", status=Task.Status.TODO)
        self.assertIsNone(task.completed_at)
        task.status = Task.Status.COMPLETED
        task.save()
        self.assertIsNotNone(task.completed_at)
        task.status = Task.Status.IN_PROGRESS
        task.save()
        self.assertIsNone(task.completed_at)

    def test_subject_must_belong_to_user(self):
        task = Task(user=self.user, subject=self.other_subject, title="Hack")
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_overdue_property(self):
        task = Task.objects.create(user=self.user, title="Retard", due_date=timezone.localdate() - timedelta(days=1))
        self.assertTrue(task.is_overdue)
        task.mark_completed()
        self.assertFalse(task.is_overdue)


class TaskViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!", name="A")
        self.other = User.objects.create_user(email="b@example.com", password="StrongPass123!", name="B")
        self.subject = Subject.objects.create(user=self.user, name="Base de données")
        self.other_subject = Subject.objects.create(user=self.other, name="Réseaux")
        self.client.login(username="a@example.com", password="StrongPass123!")

    def test_create_task(self):
        due_date = timezone.localdate() + timedelta(days=1)
        response = self.client.post(
            reverse("tasks:create"),
            {
                "title": "Terminer le TP SQL",
                "description": "Terminer les requêtes SQL demandées.",
                "subject": self.subject.pk,
                "type": Task.Type.PRACTICAL_WORK,
                "priority": Task.Priority.HIGH,
                "status": Task.Status.IN_PROGRESS,
                "due_date": due_date.isoformat(),
                "due_time": "23:59",
                "estimated_duration": "2.00",
            },
        )
        task = Task.objects.get(user=self.user, title="Terminer le TP SQL")
        self.assertRedirects(response, reverse("tasks:detail", kwargs={"pk": task.pk}))
        self.assertEqual(task.subject, self.subject)
        self.assertEqual(task.estimated_duration, Decimal("2.00"))

    def test_update_and_delete_task(self):
        task = Task.objects.create(user=self.user, subject=self.subject, title="Ancien titre")
        response = self.client.post(
            reverse("tasks:edit", kwargs={"pk": task.pk}),
            {
                "title": "Nouveau titre",
                "description": "",
                "subject": self.subject.pk,
                "type": Task.Type.HOMEWORK,
                "priority": Task.Priority.MEDIUM,
                "status": Task.Status.TODO,
                "due_date": "",
                "due_time": "",
                "estimated_duration": "1.00",
            },
        )
        self.assertRedirects(response, reverse("tasks:detail", kwargs={"pk": task.pk}))
        task.refresh_from_db()
        self.assertEqual(task.title, "Nouveau titre")

        response = self.client.post(reverse("tasks:delete", kwargs={"pk": task.pk}))
        self.assertRedirects(response, reverse("tasks:list"))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_toggle_complete_and_reopen(self):
        task = Task.objects.create(user=self.user, title="Lire chapitre")
        response = self.client.post(reverse("tasks:toggle_complete", kwargs={"pk": task.pk}))
        self.assertRedirects(response, reverse("tasks:list"))
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(task.completed_at)

        self.client.post(reverse("tasks:toggle_complete", kwargs={"pk": task.pk}))
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)
        self.assertIsNone(task.completed_at)

    def test_search_filter_and_sort(self):
        Task.objects.create(user=self.user, subject=self.subject, title="TP SQL", description="Requêtes", priority=Task.Priority.HIGH)
        Task.objects.create(user=self.user, title="Lecture Python", priority=Task.Priority.LOW)
        response = self.client.get(reverse("tasks:list"), {"q": "SQL", "priority": Task.Priority.HIGH, "sort": "priority"})
        self.assertContains(response, "TP SQL")
        self.assertNotContains(response, "Lecture Python")

    def test_user_cannot_access_other_task(self):
        other_task = Task.objects.create(user=self.other, subject=self.other_subject, title="Secret")
        response = self.client.get(reverse("tasks:detail", kwargs={"pk": other_task.pk}))
        self.assertEqual(response.status_code, 404)

    def test_form_rejects_other_user_subject(self):
        form = TaskForm(
            data={
                "title": "TP",
                "subject": self.other_subject.pk,
                "type": Task.Type.HOMEWORK,
                "priority": Task.Priority.MEDIUM,
                "status": Task.Status.TODO,
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from subjects.models import Subject

from .models import ScheduleEntry


class ScheduleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!", name="A")
        self.other = User.objects.create_user(email="b@example.com", password="StrongPass123!", name="B")
        self.subject = Subject.objects.create(user=self.user, name="Algorithmique")
        self.client.login(username="a@example.com", password="StrongPass123!")

    def test_create_update_delete_schedule_entry(self):
        response = self.client.post(
            reverse("schedule:create"),
            {
                "subject": self.subject.pk,
                "day_of_week": ScheduleEntry.Day.MONDAY,
                "start_time": "08:00",
                "end_time": "10:00",
                "room": "A04",
                "teacher": "Mme Kora",
            },
        )
        self.assertRedirects(response, reverse("schedule:list"))
        entry = ScheduleEntry.objects.get(user=self.user)
        self.assertEqual(entry.room, "A04")

        response = self.client.post(
            reverse("schedule:edit", kwargs={"pk": entry.pk}),
            {
                "subject": self.subject.pk,
                "day_of_week": ScheduleEntry.Day.TUESDAY,
                "start_time": "09:00",
                "end_time": "11:00",
                "room": "B12",
                "teacher": "Mme Kora",
            },
        )
        self.assertRedirects(response, reverse("schedule:list"))
        entry.refresh_from_db()
        self.assertEqual(entry.day_of_week, ScheduleEntry.Day.TUESDAY)

        response = self.client.post(reverse("schedule:delete", kwargs={"pk": entry.pk}))
        self.assertRedirects(response, reverse("schedule:list"))
        self.assertFalse(ScheduleEntry.objects.exists())

    def test_invalid_time_order(self):
        response = self.client.post(
            reverse("schedule:create"),
            {
                "subject": self.subject.pk,
                "day_of_week": ScheduleEntry.Day.MONDAY,
                "start_time": "10:00",
                "end_time": "08:00",
                "room": "A04",
                "teacher": "Mme Kora",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "L&#x27;heure de fin doit être après")

    def test_user_cannot_access_other_schedule_entry(self):
        other_subject = Subject.objects.create(user=self.other, name="Privé")
        entry = ScheduleEntry.objects.create(
            user=self.other,
            subject=other_subject,
            day_of_week=ScheduleEntry.Day.MONDAY,
            start_time="08:00",
            end_time="10:00",
        )
        response = self.client.get(reverse("schedule:edit", kwargs={"pk": entry.pk}))
        self.assertEqual(response.status_code, 404)

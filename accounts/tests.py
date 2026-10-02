from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_valid_registration_logs_user_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "name": "Josias Nev",
                "email": "josias@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("dashboard:index"))
        self.assertTrue(self.User.objects.filter(email="josias@example.com").exists())
        user = self.User.objects.get(email="josias@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_registration_rejects_existing_email(self):
        self.User.objects.create_user(email="josias@example.com", password="StrongPass123!", name="Josias")
        response = self.client.post(
            reverse("accounts:register"),
            {
                "name": "Autre",
                "email": "JOSIAS@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Un compte existe déjà")
        self.assertEqual(self.User.objects.filter(email__iexact="josias@example.com").count(), 1)

    def test_login_rejects_wrong_password(self):
        self.User.objects.create_user(email="student@example.com", password="StrongPass123!", name="Student")
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "student@example.com", "password": "bad-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email ou mot de passe incorrect")

    def test_valid_login_and_logout(self):
        self.User.objects.create_user(email="student@example.com", password="StrongPass123!", name="Student")
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "student@example.com", "password": "StrongPass123!"},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))

    def test_private_pages_require_authentication(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

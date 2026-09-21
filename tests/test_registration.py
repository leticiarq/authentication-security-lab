from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse


class RegistrationFlowTests(TestCase):
    registration_data = {
        "full_name": "Marina Costa",
        "email": "marina@aurora.local",
        "password": "123456",
        "password_confirmation": "123456",
        "accept_terms": True,
    }

    def test_registration_page_renders(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vamos começar")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_registration_creates_user_and_sends_local_verification(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data)

        self.assertRedirects(response, reverse("accounts:registration-complete"))
        user = get_user_model().objects.get(email="marina@aurora.local")
        self.assertEqual(user.full_name, "Marina Costa")
        self.assertFalse(user.email_verified)
        self.assertTrue(user.check_password("123456"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_verification_link_marks_email_as_verified(self):
        self.client.post(reverse("accounts:register"), self.registration_data)
        verification_url = next(
            line for line in mail.outbox[0].body.splitlines() if line.startswith("http://")
        )

        response = self.client.get(urlsplit(verification_url).path)

        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(email="marina@aurora.local")
        self.assertTrue(user.email_verified)
        self.assertContains(response, "Conta verificada")

    def test_invalid_verification_link_is_rejected(self):
        response = self.client.get(
            reverse(
                "accounts:verify-email",
                kwargs={"uidb64": "invalid", "token": "invalid-token"},
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Link indisponível", status_code=400)

    def test_verification_email_can_be_resent_from_registration_session(self):
        self.client.post(reverse("accounts:register"), self.registration_data)

        response = self.client.post(reverse("accounts:resend-verification"))

        self.assertRedirects(response, reverse("accounts:registration-complete"))
        self.assertEqual(len(mail.outbox), 2)

    def test_resend_without_registration_session_returns_to_registration(self):
        response = self.client.post(reverse("accounts:resend-verification"))

        self.assertRedirects(response, reverse("accounts:register"))

    def test_password_confirmation_must_match(self):
        data = {**self.registration_data, "password_confirmation": "654321"}

        response = self.client.post(reverse("accounts:register"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "As senhas não coincidem")
        self.assertFalse(get_user_model().objects.exists())

    def test_terms_must_be_accepted(self):
        data = {**self.registration_data, "accept_terms": False}

        response = self.client.post(reverse("accounts:register"), data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.exists())


class IntentionalWeakPasswordPolicyCharacterizationTests(TestCase):
    def test_six_digit_password_is_accepted_during_registration(self):
        """AUTH-03: preserve the vulnerable baseline until remediation work."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "full_name": "Conta de Laboratório",
                "email": "weak-policy@example.local",
                "password": "123456",
                "password_confirmation": "123456",
                "accept_terms": True,
            },
        )

        self.assertRedirects(response, reverse("accounts:registration-complete"))
        self.assertTrue(get_user_model().objects.filter(email="weak-policy@example.local").exists())

    def test_fewer_than_six_characters_is_rejected(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "full_name": "Conta de Laboratório",
                "email": "too-short@example.local",
                "password": "12345",
                "password_confirmation": "12345",
                "accept_terms": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.exists())

from datetime import timedelta
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from authentication.models import PasswordResetRequest
from authentication.services import generate_password_reset_token


class PasswordRecoveryFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="recovery@example.local",
            password="old-password",
            full_name="Recovery User",
            email_verified=True,
        )

    def request_reset(self):
        return self.client.post(
            reverse("authentication:password-recovery"),
            {"email": self.user.email},
        )

    def reset_path_from_email(self):
        reset_url = next(
            line for line in mail.outbox[-1].body.splitlines() if line.startswith("http://")
        )
        return urlsplit(reset_url).path

    def test_existing_account_receives_local_reset_email(self):
        response = self.request_reset()

        self.assertRedirects(response, reverse("authentication:password-recovery-sent"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        reset_request = PasswordResetRequest.objects.get()
        self.assertRegex(reset_request.token, r"^\d{6}$")
        self.assertFalse(reset_request.is_used)

    def test_reset_link_changes_password_and_is_consumed(self):
        self.request_reset()
        reset_path = self.reset_path_from_email()

        form = self.client.get(reset_path)
        response = self.client.post(
            reset_path,
            {"password": "654321", "password_confirmation": "654321"},
        )

        self.assertEqual(form.status_code, 200)
        self.assertRedirects(response, reverse("authentication:password-reset-complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("654321"))
        self.assertTrue(PasswordResetRequest.objects.get().is_used)
        self.assertEqual(self.client.get(reset_path).status_code, 400)

    def test_expired_reset_link_is_rejected(self):
        reset = PasswordResetRequest.objects.create(
            user=self.user,
            token="123456",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        path = reverse(
            "authentication:password-reset",
            kwargs={"uidb64": uid, "token": reset.token},
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Link indisponível", status_code=400)


class IntentionalRecoveryEnumerationCharacterizationTests(TestCase):
    def test_unknown_account_has_different_response_and_no_email(self):
        response = self.client.post(
            reverse("authentication:password-recovery"),
            {"email": "missing@example.local"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Não foi possível localizar o acesso")
        self.assertEqual(len(mail.outbox), 0)


class IntentionalPredictableTokenCharacterizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="token@example.local",
            password="token-password",
            full_name="Token User",
        )

    def test_token_is_deterministic_inside_one_minute_bucket(self):
        first = generate_password_reset_token(self.user, timestamp=1_800_000_001)
        second = generate_password_reset_token(self.user, timestamp=1_800_000_059)

        self.assertEqual(first, second)
        self.assertRegex(first, r"^\d{6}$")

    def test_different_minute_changes_token(self):
        first = generate_password_reset_token(self.user, timestamp=1_800_000_001)
        second = generate_password_reset_token(self.user, timestamp=1_800_000_061)

        self.assertNotEqual(first, second)

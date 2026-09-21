from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from authentication.models import Device, LoginSession


class SessionManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="sessions@example.local",
            password="session-password",
            full_name="Session User",
            email_verified=True,
        )

    def login_client(self, client, user_agent):
        response = client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "session-password"},
            HTTP_USER_AGENT=user_agent,
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertRedirects(response, reverse("authentication:dashboard"))
        return response

    def test_login_registers_session_and_device(self):
        self.login_client(self.client, "Mozilla/5.0 Chrome/120 Linux")

        session = LoginSession.objects.get()
        device = Device.objects.get()
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.device, device)
        self.assertEqual(session.django_session_key, self.client.session.session_key)
        self.assertEqual(device.name, "Chrome em Linux")

    def test_session_and_history_pages_are_authenticated(self):
        self.login_client(self.client, "Mozilla/5.0 Firefox/120 Windows")

        sessions = self.client.get(reverse("authentication:sessions"))
        history = self.client.get(reverse("authentication:login-history"))

        self.assertEqual(sessions.status_code, 200)
        self.assertContains(sessions, "Firefox em Windows")
        self.assertEqual(history.status_code, 200)
        self.assertContains(history, "Concluído")

    def test_logout_marks_inventory_session_revoked(self):
        self.login_client(self.client, "Test Browser")
        session = LoginSession.objects.get()

        self.client.post(reverse("authentication:logout"))

        session.refresh_from_db()
        self.assertIsNotNone(session.revoked_at)


class IntentionalCookieConfigurationCharacterizationTests(TestCase):
    def test_session_cookie_is_not_httponly_or_secure(self):
        user = get_user_model().objects.create_user(
            email="cookie@example.local",
            password="cookie-password",
            full_name="Cookie User",
            email_verified=True,
        )

        response = self.client.post(
            reverse("authentication:login"),
            {"email": user.email, "password": "cookie-password"},
        )
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]

        self.assertFalse(cookie["httponly"])
        self.assertFalse(cookie["secure"])


class IntentionalSessionInvalidationCharacterizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="revoke@example.local",
            password="revoke-password",
            full_name="Revoke User",
            email_verified=True,
        )
        self.first = Client()
        self.second = Client()
        for client, agent in ((self.first, "First Chrome"), (self.second, "Second Firefox")):
            response = client.post(
                reverse("authentication:login"),
                {"email": self.user.email, "password": "revoke-password"},
                HTTP_USER_AGENT=agent,
            )
            self.assertEqual(response.status_code, 302)

    def test_revoked_session_inventory_does_not_invalidate_django_session(self):
        second_session = LoginSession.objects.get(
            django_session_key=self.second.session.session_key
        )

        response = self.first.post(
            reverse("authentication:revoke-session", args=[second_session.id])
        )
        second_dashboard = self.second.get(reverse("authentication:dashboard"))

        self.assertRedirects(response, reverse("authentication:sessions"))
        second_session.refresh_from_db()
        self.assertIsNotNone(second_session.revoked_at)
        self.assertEqual(second_dashboard.status_code, 200)

    def test_revoke_other_sessions_only_updates_inventory(self):
        response = self.first.post(reverse("authentication:revoke-other-sessions"))

        self.assertRedirects(response, reverse("authentication:sessions"))
        self.assertEqual(LoginSession.objects.filter(revoked_at__isnull=True).count(), 1)
        self.assertEqual(self.second.get(reverse("authentication:dashboard")).status_code, 200)

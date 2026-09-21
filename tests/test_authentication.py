from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from authentication.middleware import REMEMBER_COOKIE_NAME
from authentication.models import LoginAttempt
from authentication.services import check_credentials


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="ana@aurora.local",
            password="senha-de-teste",
            full_name="Ana Ribeiro",
            email_verified=True,
        )

    def test_login_and_authenticated_dashboard(self):
        response = self.client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "senha-de-teste"},
        )

        self.assertRedirects(response, reverse("authentication:dashboard"))
        dashboard = self.client.get(reverse("authentication:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Olá, Ana")
        attempt = LoginAttempt.objects.get()
        self.assertTrue(attempt.successful)
        self.assertEqual(attempt.user, self.user)

    def test_dashboard_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("authentication:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('authentication:login')}?next={reverse('authentication:dashboard')}",
        )

    def test_logout_requires_post_and_clears_session(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("authentication:logout")).status_code, 405)
        response = self.client.post(reverse("authentication:logout"))

        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_external_next_url_is_not_used(self):
        response = self.client.post(
            f"{reverse('authentication:login')}?next=https://example.com/",
            {"email": self.user.email, "password": "senha-de-teste"},
        )

        self.assertRedirects(response, reverse("authentication:dashboard"))

    def test_unverified_account_cannot_open_authenticated_area(self):
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])

        response = self.client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "senha-de-teste"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirme seu e-mail")
        self.assertNotIn("_auth_user_id", self.client.session)


class IntentionalEnumerationCharacterizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="known@example.local",
            password="known-password",
            full_name="Known User",
        )

    def test_existing_and_unknown_accounts_receive_different_errors(self):
        unknown = self.client.post(
            reverse("authentication:login"),
            {"email": "missing@example.local", "password": "wrong-password"},
        )
        existing = Client().post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "wrong-password"},
        )

        self.assertContains(unknown, "Não foi possível localizar o acesso")
        self.assertContains(existing, "Não foi possível validar o acesso")

    def test_unknown_account_skips_password_hash_work(self):
        user_model = get_user_model()
        with patch.object(user_model, "check_password", return_value=False) as password_check:
            check_credentials(self.user.email, "wrong-password")
            self.assertEqual(password_check.call_count, 1)

            password_check.reset_mock()
            check_credentials("missing@example.local", "wrong-password")
            password_check.assert_not_called()


class IntentionalAttemptRestrictionCharacterizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="locked@example.local",
            password="correct-password",
            full_name="Locked User",
            email_verified=True,
        )

    def test_new_browser_session_bypasses_attempt_lock(self):
        login_url = reverse("authentication:login")
        for _ in range(5):
            self.client.post(
                login_url,
                {"email": self.user.email, "password": "wrong-password"},
            )

        blocked = self.client.post(
            login_url,
            {"email": self.user.email, "password": "correct-password"},
        )
        fresh_client = Client()
        allowed = fresh_client.post(
            login_url,
            {"email": self.user.email, "password": "correct-password"},
        )

        self.assertContains(blocked, "Muitas tentativas")
        self.assertRedirects(allowed, reverse("authentication:dashboard"))


class IntentionalRememberMeCharacterizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="remember@example.local",
            password="remember-password",
            full_name="Remember User",
            email_verified=True,
        )

    def test_remember_cookie_is_raw_user_id_and_restores_login(self):
        response = self.client.post(
            reverse("authentication:login"),
            {
                "email": self.user.email,
                "password": "remember-password",
                "remember_me": True,
            },
        )
        cookie = response.cookies[REMEMBER_COOKIE_NAME]

        fresh_client = Client()
        fresh_client.cookies[REMEMBER_COOKIE_NAME] = cookie.value
        dashboard = fresh_client.get(reverse("authentication:dashboard"))

        self.assertEqual(cookie.value, str(self.user.pk))
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(str(fresh_client.session["_auth_user_id"]), str(self.user.pk))

    def test_remember_cookie_remains_valid_after_password_change(self):
        response = self.client.post(
            reverse("authentication:login"),
            {
                "email": self.user.email,
                "password": "remember-password",
                "remember_me": True,
            },
        )
        cookie_value = response.cookies[REMEMBER_COOKIE_NAME].value
        self.user.set_password("a-new-password")
        self.user.save(update_fields=["password"])

        fresh_client = Client()
        fresh_client.cookies[REMEMBER_COOKIE_NAME] = cookie_value

        self.assertEqual(fresh_client.get(reverse("authentication:dashboard")).status_code, 200)

    def test_regular_login_does_not_set_remember_cookie(self):
        response = self.client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "remember-password"},
        )

        self.assertNotIn(REMEMBER_COOKIE_NAME, response.cookies)


class IntentionalDefaultCredentialCharacterizationTests(TestCase):
    def test_seed_restores_documented_demo_credential(self):
        output = StringIO()

        call_command("seed_dev", stdout=output)
        call_command("seed_dev", stdout=output)

        users = get_user_model().objects.filter(email="demo@vaulta.local")
        self.assertEqual(users.count(), 1)
        self.assertTrue(users.get().check_password("vaulta-demo"))
        self.assertIn("Conta demo atualizada", output.getvalue())

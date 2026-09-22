import hashlib

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserPreference
from authentication.models import AuthenticationDiagnostic, LegacyCredential
from organizations.models import Organization


class ProfileAndPreferenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="profile@example.local",
            password="current-password",
            full_name="Profile User",
            email_verified=True,
        )
        self.client.force_login(self.user)

    def test_profile_and_preferences_can_be_updated(self):
        profile_response = self.client.post(
            reverse("accounts:profile"),
            {"full_name": "Updated User", "email": "updated@example.local"},
        )
        preference_response = self.client.post(
            reverse("accounts:preferences"),
            {
                "locale": "pt-BR",
                "timezone": "America/Sao_Paulo",
                "currency": "BRL",
                "notify_security": True,
            },
        )

        self.assertRedirects(profile_response, reverse("accounts:profile"))
        self.assertRedirects(preference_response, reverse("accounts:preferences"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated User")
        self.assertEqual(
            UserPreference.objects.get(user=self.user).timezone,
            "America/Sao_Paulo",
        )

    def test_password_change_accepts_weak_password_and_preserves_current_session(self):
        response = self.client.post(
            reverse("accounts:password-change"),
            {
                "current_password": "current-password",
                "new_password": "123456",
                "confirmation": "123456",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("123456"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)


class SystemAdministrationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="system@example.local",
            password="system-password",
            full_name="System Admin",
            email_verified=True,
            role=user_model.Role.SYSTEM_ADMIN,
        )
        self.regular = user_model.objects.create_user(
            email="regular@example.local",
            password="regular-password",
            full_name="Regular User",
            email_verified=True,
        )
        Organization.objects.create(name="Admin Test Org", slug="admin-test")

    def test_system_admin_can_open_control_pages_and_toggle_user(self):
        self.client.force_login(self.admin)

        self.assertEqual(self.client.get(reverse("administration:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("administration:users")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("administration:organizations")).status_code,
            200,
        )
        response = self.client.post(
            reverse("administration:toggle-user-status", args=[self.regular.id])
        )

        self.assertRedirects(response, reverse("administration:users"))
        self.regular.refresh_from_db()
        self.assertFalse(self.regular.is_active)

    def test_regular_user_is_forbidden_from_control_area(self):
        self.client.force_login(self.regular)

        self.assertEqual(self.client.get(reverse("administration:dashboard")).status_code, 403)


class IntentionalLegacyCredentialCharacterizationTests(TestCase):
    def test_unsalted_sha1_credential_authenticates_legacy_user(self):
        user = get_user_model().objects.create_user(
            email="legacy-test@example.local",
            password=None,
            full_name="Legacy Test",
            email_verified=True,
        )
        expected_digest = hashlib.sha1(b"welcome123", usedforsecurity=False).hexdigest()
        credential = LegacyCredential.objects.create(
            user=user,
            legacy_digest=expected_digest,
        )

        response = self.client.post(
            reverse("authentication:login"),
            {"email": user.email, "password": "welcome123"},
        )

        self.assertEqual(credential.legacy_digest, expected_digest)
        self.assertEqual(len(credential.legacy_digest), 40)
        self.assertRedirects(response, reverse("authentication:dashboard"))


class IntentionalCredentialExposureCharacterizationTests(TestCase):
    def test_raw_login_password_is_available_in_admin_diagnostics(self):
        user_model = get_user_model()
        target = user_model.objects.create_user(
            email="telemetry@example.local",
            password="actual-password",
            full_name="Telemetry User",
            email_verified=True,
        )
        admin = user_model.objects.create_user(
            email="support-admin@example.local",
            password="admin-password",
            full_name="Support Admin",
            email_verified=True,
            role=user_model.Role.SYSTEM_ADMIN,
        )

        self.client.post(
            reverse("authentication:login"),
            {"email": target.email, "password": "captured-password"},
        )
        event = AuthenticationDiagnostic.objects.get()
        self.client.force_login(admin)
        response = self.client.get(reverse("administration:diagnostics"))

        self.assertEqual(event.payload["password"], ["captured-password"])
        self.assertContains(response, "captured-password")

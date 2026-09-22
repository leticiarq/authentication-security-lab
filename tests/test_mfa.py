from datetime import timedelta

from authentication.models import Device, MFAProfile, RecoveryCode
from authentication.totp import code_at, generate_secret, verify_code
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone


class TOTPTests(TestCase):
    def test_generated_code_verifies_in_same_time_window(self):
        secret = generate_secret()
        timestamp = 1_800_000_000

        self.assertTrue(verify_code(secret, code_at(secret, timestamp), timestamp))
        self.assertFalse(verify_code(secret, "000000", timestamp))


class MFASetupTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="mfa-setup@example.local",
            password="mfa-password",
            full_name="MFA Setup",
            email_verified=True,
        )
        self.client.force_login(self.user)

    def test_user_can_enable_mfa_and_receives_recovery_codes_once(self):
        setup_url = reverse("authentication:mfa-setup")
        self.client.get(setup_url)
        profile = MFAProfile.objects.get(user=self.user)

        response = self.client.post(setup_url, {"code": code_at(profile.secret)})
        settings_page = self.client.get(reverse("authentication:security-settings"))

        self.assertRedirects(response, reverse("authentication:security-settings"))
        profile.refresh_from_db()
        self.assertTrue(profile.is_enabled)
        self.assertEqual(RecoveryCode.objects.filter(mfa_profile=profile).count(), 8)
        self.assertContains(settings_page, "Salve seus códigos de recuperação")
        self.assertNotContains(
            self.client.get(reverse("authentication:security-settings")),
            "Salve seus códigos de recuperação",
        )


class MFAAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="mfa-login@example.local",
            password="mfa-password",
            full_name="MFA Login",
            email_verified=True,
        )
        self.profile = MFAProfile.objects.create(
            user=self.user,
            secret=generate_secret(),
            enabled_at=timezone.now(),
        )

    def test_password_stage_redirects_to_mfa_challenge(self):
        response = self.client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "mfa-password"},
        )

        self.assertRedirects(response, reverse("authentication:mfa-challenge"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(self.client.session["password_verified"])

    def test_valid_totp_completes_login(self):
        self.client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "mfa-password"},
        )

        response = self.client.post(
            reverse("authentication:mfa-challenge"),
            {"code": code_at(self.profile.secret)},
        )

        self.assertRedirects(response, reverse("authentication:dashboard"))
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(self.user.pk))

    def test_recovery_code_is_single_use(self):
        from authentication.services import generate_recovery_codes

        plain_code = generate_recovery_codes(self.profile, amount=1)[0]
        self.client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "mfa-password"},
        )
        first = self.client.post(
            reverse("authentication:mfa-challenge"),
            {"code": plain_code},
        )
        self.client.post(reverse("authentication:logout"))
        self.client.post(
            reverse("authentication:login"),
            {"email": self.user.email, "password": "mfa-password"},
        )
        second = self.client.post(
            reverse("authentication:mfa-challenge"),
            {"code": plain_code},
        )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 200)
        self.assertContains(second, "não é válido")


class IntentionalSessionFixationCharacterizationTests(TestCase):
    def test_session_key_is_not_rotated_when_mfa_completes(self):
        user = get_user_model().objects.create_user(
            email="fixed@example.local",
            password="fixed-password",
            full_name="Fixed Session",
            email_verified=True,
        )
        profile = MFAProfile.objects.create(
            user=user,
            secret=generate_secret(),
            enabled_at=timezone.now(),
        )
        self.client.post(
            reverse("authentication:login"),
            {"email": user.email, "password": "fixed-password"},
        )
        pre_auth_key = self.client.session.session_key

        self.client.post(
            reverse("authentication:mfa-challenge"),
            {"code": code_at(profile.secret)},
        )

        self.assertEqual(self.client.session.session_key, pre_auth_key)


class IntentionalTrustedDeviceCharacterizationTests(TestCase):
    def test_trusted_device_from_another_user_skips_victim_mfa(self):
        user_model = get_user_model()
        victim = user_model.objects.create_user(
            email="victim@example.local",
            password="victim-password",
            full_name="Victim User",
            email_verified=True,
        )
        other = user_model.objects.create_user(
            email="other-device@example.local",
            password="other-password",
            full_name="Other Device",
            email_verified=True,
        )
        MFAProfile.objects.create(
            user=victim,
            secret=generate_secret(),
            enabled_at=timezone.now(),
        )
        trusted_device = Device.objects.create(
            user=other,
            name="Other trusted device",
            fingerprint="a" * 64,
            trusted_until=timezone.now() + timedelta(days=30),
        )
        client = Client()
        client.cookies["vaulta_trusted_device"] = str(trusted_device.id)

        response = client.post(
            reverse("authentication:login"),
            {"email": victim.email, "password": "victim-password"},
        )

        self.assertRedirects(response, reverse("authentication:dashboard"))
        self.assertEqual(str(client.session["_auth_user_id"]), str(victim.pk))

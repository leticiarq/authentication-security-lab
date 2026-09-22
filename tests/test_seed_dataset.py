from io import StringIO

from authentication.models import Device, LoginAttempt, LoginSession
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from finance.models import FinancialAccount, Notification, Transaction
from organizations.models import Invitation, Membership, Organization


class DevelopmentSeedDatasetTests(TestCase):
    def setUp(self):
        self.output = StringIO()
        call_command("seed_dev", stdout=self.output)

    def dataset_counts(self):
        return {
            "users": get_user_model().objects.count(),
            "organizations": Organization.objects.count(),
            "memberships": Membership.objects.count(),
            "accounts": FinancialAccount.objects.count(),
            "transactions": Transaction.objects.count(),
            "notifications": Notification.objects.count(),
            "invitations": Invitation.objects.count(),
            "devices": Device.objects.count(),
            "sessions": LoginSession.objects.count(),
            "attempts": LoginAttempt.objects.count(),
        }

    def test_seed_populates_multiple_realistic_tenants(self):
        self.assertEqual(
            self.dataset_counts(),
            {
                "users": 7,
                "organizations": 3,
                "memberships": 5,
                "accounts": 4,
                "transactions": 8,
                "notifications": 7,
                "invitations": 2,
                "devices": 3,
                "sessions": 3,
                "attempts": 5,
            },
        )
        self.assertIn("Dataset fictício pronto", self.output.getvalue())

    def test_seed_is_idempotent(self):
        initial_counts = self.dataset_counts()

        call_command("seed_dev", stdout=StringIO())

        self.assertEqual(self.dataset_counts(), initial_counts)

    def test_seeded_users_can_open_their_own_financial_workspace(self):
        response = self.client.post(
            reverse("authentication:login"),
            {"email": "marina@nebula.local", "password": "nebula-local"},
        )

        self.assertRedirects(response, reverse("authentication:dashboard"))
        dashboard = self.client.get(reverse("authentication:dashboard"))
        self.assertContains(dashboard, "Nébula Comércio")
        self.assertContains(dashboard, "108.040,15")
        self.assertNotContains(dashboard, "Aurora Studio")

    def test_seeded_security_inventory_is_visible_to_demo_user(self):
        self.client.post(
            reverse("authentication:login"),
            {"email": "demo@vaulta.local", "password": "vaulta-demo"},
        )

        sessions = self.client.get(reverse("authentication:sessions"))
        history = self.client.get(reverse("authentication:login-history"))

        self.assertContains(sessions, "Notebook Linux — Firefox")
        self.assertContains(sessions, "Celular — Chrome")
        self.assertContains(history, "Safari 17 · macOS")

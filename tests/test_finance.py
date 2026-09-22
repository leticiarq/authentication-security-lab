from datetime import timedelta
from decimal import Decimal

from authentication.models import PasswordResetRequest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from finance.models import FinancialAccount, Notification, Transaction
from organizations.models import Membership, Organization


class FinancialDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="finance@example.local",
            password="finance-password",
            full_name="Finance User",
            email_verified=True,
        )
        self.organization = Organization.objects.create(name="Orion", slug="orion")
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Membership.Role.ADMIN,
        )
        self.account = FinancialAccount.objects.create(
            organization=self.organization,
            name="Conta Operacional",
            type=FinancialAccount.Type.CHECKING,
            balance=Decimal("15000.00"),
        )
        Transaction.objects.create(
            account=self.account,
            description="Receita fictícia",
            amount=Decimal("2500.00"),
            direction=Transaction.Direction.INCOME,
            category="Recebimentos",
            occurred_on=timezone.localdate(),
        )
        Transaction.objects.create(
            account=self.account,
            description="Despesa fictícia",
            amount=Decimal("800.00"),
            direction=Transaction.Direction.EXPENSE,
            category="Operacional",
            occurred_on=timezone.localdate() - timedelta(days=1),
        )
        self.client.force_login(self.user)

    def test_dashboard_uses_persisted_financial_data(self):
        response = self.client.get(reverse("authentication:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "15.000,00")
        self.assertContains(response, "Receita fictícia")

    def test_summary_api_is_authenticated_and_tenant_scoped(self):
        response = self.client.get(reverse("finance:dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "organization": "Orion",
                "balance": "15000.00",
                "income": "2500.00",
                "expenses": "800.00",
            },
        )
        self.client.logout()
        self.assertIn(
            self.client.get(reverse("finance:dashboard-summary")).status_code,
            {401, 403},
        )

    def test_notifications_can_be_marked_read(self):
        notification = Notification.objects.create(
            user=self.user,
            kind=Notification.Kind.FINANCE,
            title="Atualização fictícia",
            body="Uma informação financeira simulada.",
        )

        page = self.client.get(reverse("finance:notifications"))
        response = self.client.post(reverse("finance:mark-read"))

        self.assertContains(page, notification.title)
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)


class IntentionalAssistedRecoveryCharacterizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.local",
            password="owner-password",
            full_name="Owner User",
            email_verified=True,
        )
        organization = Organization.objects.create(name="Shared Finance", slug="shared-finance")
        Membership.objects.create(
            user=self.user,
            organization=organization,
            role=Membership.Role.ADMIN,
        )
        account = FinancialAccount.objects.create(
            organization=organization,
            name="Shared Account",
            type=FinancialAccount.Type.CHECKING,
        )
        Transaction.objects.create(
            account=account,
            description="Known shared transaction",
            amount=Decimal("431.90"),
            direction=Transaction.Direction.EXPENSE,
            category="Operacional",
            occurred_on=timezone.localdate(),
        )

    def test_shared_financial_value_grants_direct_password_reset(self):
        response = self.client.post(
            reverse("authentication:assisted-password-recovery"),
            {
                "email": self.user.email,
                "organization_name": "Shared Finance",
                "latest_transaction_amount": "431.90",
            },
        )

        reset_request = PasswordResetRequest.objects.get(user=self.user)
        self.assertRedirects(
            response,
            reverse(
                "authentication:password-reset",
                kwargs={
                    "uidb64": urlsafe_base64_encode(force_bytes(self.user.pk)),
                    "token": reset_request.token,
                },
            ),
        )

    def test_incorrect_financial_value_is_rejected(self):
        response = self.client.post(
            reverse("authentication:assisted-password-recovery"),
            {
                "email": self.user.email,
                "organization_name": "Shared Finance",
                "latest_transaction_amount": "431.91",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Não foi possível validar")
        self.assertFalse(PasswordResetRequest.objects.exists())

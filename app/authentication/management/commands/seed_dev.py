import hashlib
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import FinancialAccount, Notification, Transaction
from organizations.models import Membership, Organization

from authentication.models import LegacyCredential


class Command(BaseCommand):
    help = "Cria dados fictícios mínimos para o ambiente local da Vaulta."

    def handle(self, *args, **options):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            email="demo@vaulta.local",
            defaults={
                "full_name": "Conta Demonstração",
                "email_verified": True,
            },
        )
        user.full_name = "Conta Demonstração"
        user.email_verified = True
        user.is_active = True

        # INTENTIONAL LAB BEHAVIOR (AUTH-15): the development seed always
        # restores a documented default credential. This is useful only for the
        # isolated exercise and must never exist in a production bootstrap.
        user.set_password("vaulta-demo")
        user.save()

        organization, _ = Organization.objects.update_or_create(
            slug="aurora-studio",
            defaults={
                "name": "Aurora Studio",
                "status": Organization.Status.ACTIVE,
                "plan": Organization.Plan.ESSENTIAL,
            },
        )
        Membership.objects.update_or_create(
            user=user,
            organization=organization,
            defaults={"role": Membership.Role.ADMIN},
        )

        analyst, _ = user_model.objects.get_or_create(
            email="analista@aurora.local",
            defaults={
                "full_name": "Rafael Nunes",
                "email_verified": True,
            },
        )
        analyst.full_name = "Rafael Nunes"
        analyst.email_verified = True
        analyst.set_unusable_password()
        analyst.save()
        Membership.objects.update_or_create(
            user=analyst,
            organization=organization,
            defaults={"role": Membership.Role.MEMBER},
        )

        operating_account, _ = FinancialAccount.objects.update_or_create(
            organization=organization,
            name="Conta Operacional",
            defaults={
                "type": FinancialAccount.Type.CHECKING,
                "balance": "128450.00",
                "currency": "BRL",
            },
        )
        FinancialAccount.objects.update_or_create(
            organization=organization,
            name="Reserva Estratégica",
            defaults={
                "type": FinancialAccount.Type.RESERVE,
                "balance": "56270.00",
                "currency": "BRL",
            },
        )
        today = timezone.localdate()
        transaction_rows = (
            ("Projeto Horizonte", "8400.00", Transaction.Direction.INCOME, "Recebimentos", 0),
            ("Infraestrutura Cloud", "1280.00", Transaction.Direction.EXPENSE, "Tecnologia", 1),
            ("Espaço de trabalho", "3200.00", Transaction.Direction.EXPENSE, "Operacional", 3),
            ("Contrato Polaris", "12450.00", Transaction.Direction.INCOME, "Recebimentos", 6),
        )
        for description, amount, direction, category, days_ago in transaction_rows:
            Transaction.objects.update_or_create(
                account=operating_account,
                description=description,
                occurred_on=today - timedelta(days=days_ago),
                defaults={"amount": amount, "direction": direction, "category": category},
            )

        notification_rows = (
            (
                Notification.Kind.FINANCE,
                "Recebimento confirmado",
                "O lançamento Projeto Horizonte foi conciliado.",
            ),
            (
                Notification.Kind.TEAM,
                "Equipe atualizada",
                "Rafael Nunes faz parte da Aurora Studio.",
            ),
            (
                Notification.Kind.SECURITY,
                "Novo acesso registrado",
                "Um novo navegador foi associado à sua conta.",
            ),
        )
        for kind, title, body in notification_rows:
            Notification.objects.get_or_create(
                user=user,
                title=title,
                defaults={"kind": kind, "body": body},
            )

        system_admin, _ = user_model.objects.get_or_create(
            email="admin@vaulta.local",
            defaults={"full_name": "Administração Vaulta"},
        )
        system_admin.full_name = "Administração Vaulta"
        system_admin.role = user_model.Role.SYSTEM_ADMIN
        system_admin.email_verified = True
        system_admin.is_active = True
        system_admin.set_password("vaulta-admin")
        system_admin.save()

        legacy_user, _ = user_model.objects.get_or_create(
            email="legacy@vaulta.local",
            defaults={"full_name": "Conta Legada", "email_verified": True},
        )
        legacy_user.full_name = "Conta Legada"
        legacy_user.email_verified = True
        legacy_user.is_active = True
        legacy_user.set_unusable_password()
        legacy_user.save()
        LegacyCredential.objects.update_or_create(
            user=legacy_user,
            defaults={
                # INTENTIONAL LAB BEHAVIOR (AUTH-05): unsalted SHA-1 for a
                # fictitious legacy account. Never use this in production.
                "legacy_digest": hashlib.sha1(
                    b"welcome123",
                    usedforsecurity=False,
                ).hexdigest()
            },
        )

        action = "criada" if created else "atualizada"
        self.stdout.write(self.style.SUCCESS(f"Conta demo {action}: demo@vaulta.local"))

import hashlib
from datetime import timedelta

from accounts.models import UserPreference
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import FinancialAccount, Notification, Transaction
from organizations.models import Invitation, Membership, Organization

from authentication.models import Device, LegacyCredential, LoginAttempt, LoginSession


class Command(BaseCommand):
    help = "Cria o conjunto de dados inteiramente fictício do laboratório local da Vaulta."

    def handle(self, *args, **options):
        user_model = get_user_model()

        def provision_user(email, full_name, password, role=user_model.Role.REGULAR):
            account, was_created = user_model.objects.get_or_create(email=email)
            account.full_name = full_name
            account.role = role
            account.email_verified = True
            account.is_active = True
            if password is None:
                account.set_unusable_password()
            else:
                account.set_password(password)
            account.save()
            UserPreference.objects.update_or_create(
                user=account,
                defaults={
                    "locale": "pt-BR",
                    "timezone": "America/Recife",
                    "currency": "BRL",
                    "notify_financial": True,
                    "notify_security": True,
                    "notify_team": True,
                },
            )
            return account, was_created

        # INTENTIONAL LAB BEHAVIOR (AUTH-15): the development seed always
        # restores a documented default credential. This is useful only for the
        # isolated exercise and must never exist in a production bootstrap.
        user, created = provision_user(
            "demo@vaulta.local",
            "Conta Demonstração",
            "vaulta-demo",
        )

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

        analyst, _ = provision_user(
            "analista@aurora.local",
            "Rafael Nunes",
            "aurora-analista",
        )
        Membership.objects.update_or_create(
            user=analyst,
            organization=organization,
            defaults={"role": Membership.Role.MEMBER},
        )

        finance_user, _ = provision_user(
            "financeiro@aurora.local",
            "Bianca Torres",
            "fluxo-2024",
        )
        Membership.objects.update_or_create(
            user=finance_user,
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

        Notification.objects.update_or_create(
            user=finance_user,
            title="Conciliação pendente",
            defaults={
                "kind": Notification.Kind.FINANCE,
                "body": "Dois lançamentos fictícios aguardam revisão da equipe financeira.",
            },
        )
        Invitation.objects.update_or_create(
            organization=organization,
            email="parcerias@aurora.local",
            defaults={
                "role": Membership.Role.MEMBER,
                "expires_at": timezone.now() + timedelta(days=5),
                "accepted_at": None,
                "invited_by": user,
            },
        )

        nebula_admin, _ = provision_user(
            "marina@nebula.local",
            "Marina Costa",
            "nebula-local",
        )
        nebula_member, _ = provision_user(
            "caio@nebula.local",
            "Caio Mendes",
            "vendas-2025",
        )
        nebula, _ = Organization.objects.update_or_create(
            slug="nebula-comercio",
            defaults={
                "name": "Nébula Comércio",
                "status": Organization.Status.ACTIVE,
                "plan": Organization.Plan.GROWTH,
            },
        )
        Membership.objects.update_or_create(
            user=nebula_admin,
            organization=nebula,
            defaults={"role": Membership.Role.ADMIN},
        )
        Membership.objects.update_or_create(
            user=nebula_member,
            organization=nebula,
            defaults={"role": Membership.Role.MEMBER},
        )

        nebula_account, _ = FinancialAccount.objects.update_or_create(
            organization=nebula,
            name="Conta Principal",
            defaults={
                "type": FinancialAccount.Type.CHECKING,
                "balance": "84290.15",
                "currency": "BRL",
            },
        )
        FinancialAccount.objects.update_or_create(
            organization=nebula,
            name="Recebíveis Marketplace",
            defaults={
                "type": FinancialAccount.Type.RECEIVABLES,
                "balance": "23750.00",
                "currency": "BRL",
            },
        )
        nebula_transactions = (
            ("Vendas marketplace", "6310.40", Transaction.Direction.INCOME, "Vendas", 0),
            ("Operador logístico", "2190.75", Transaction.Direction.EXPENSE, "Logística", 2),
            ("Campanha de inverno", "1450.00", Transaction.Direction.EXPENSE, "Marketing", 5),
            ("Repasse de parceiros", "9780.20", Transaction.Direction.INCOME, "Vendas", 8),
        )
        for description, amount, direction, category, days_ago in nebula_transactions:
            Transaction.objects.update_or_create(
                account=nebula_account,
                description=description,
                occurred_on=today - timedelta(days=days_ago),
                defaults={"amount": amount, "direction": direction, "category": category},
            )

        for target, title, body, kind in (
            (
                nebula_admin,
                "Resumo semanal disponível",
                "O consolidado fictício da Nébula Comércio já pode ser consultado.",
                Notification.Kind.FINANCE,
            ),
            (
                nebula_admin,
                "Convite aguardando resposta",
                "Um convite da organização ainda não foi aceito.",
                Notification.Kind.TEAM,
            ),
            (
                nebula_member,
                "Acesso reconhecido",
                "Seu navegador local foi associado ao workspace.",
                Notification.Kind.SECURITY,
            ),
        ):
            Notification.objects.update_or_create(
                user=target,
                title=title,
                defaults={"kind": kind, "body": body},
            )

        Invitation.objects.update_or_create(
            organization=nebula,
            email="auditoria@nebula.local",
            defaults={
                "role": Membership.Role.MEMBER,
                "expires_at": timezone.now() + timedelta(days=4),
                "accepted_at": None,
                "invited_by": nebula_admin,
            },
        )
        Organization.objects.update_or_create(
            slug="horizonte-logistica",
            defaults={
                "name": "Horizonte Logística",
                "status": Organization.Status.SUSPENDED,
                "plan": Organization.Plan.ESSENTIAL,
            },
        )

        system_admin, _ = provision_user(
            "admin@vaulta.local",
            "Administração Vaulta",
            "vaulta-admin",
            role=user_model.Role.SYSTEM_ADMIN,
        )

        legacy_user, _ = provision_user(
            "legacy@vaulta.local",
            "Conta Legada",
            None,
        )
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

        device_rows = (
            (
                user,
                "Notebook Linux — Firefox",
                "seed-demo-linux-firefox",
                1,
                20,
                "seed-demo-linux-session-0001",
                "192.0.2.44",
            ),
            (
                user,
                "Celular — Chrome",
                "seed-demo-mobile-chrome",
                4,
                None,
                "seed-demo-mobile-session-0002",
                "198.51.100.27",
            ),
            (
                nebula_admin,
                "Notebook comercial — Chrome",
                "seed-nebula-admin-chrome",
                2,
                12,
                "seed-nebula-admin-session-0001",
                "203.0.113.18",
            ),
        )
        for (
            device_user,
            name,
            fingerprint,
            last_seen_days,
            trusted_days,
            session_key,
            source_ip,
        ) in device_rows:
            last_seen_at = timezone.now() - timedelta(days=last_seen_days)
            trusted_until = (
                timezone.now() + timedelta(days=trusted_days) if trusted_days is not None else None
            )
            device, _ = Device.objects.update_or_create(
                user=device_user,
                fingerprint=fingerprint,
                defaults={
                    "name": name,
                    "last_seen_at": last_seen_at,
                    "trusted_until": trusted_until,
                    "revoked_at": None,
                },
            )
            session, _ = LoginSession.objects.update_or_create(
                django_session_key=session_key,
                defaults={
                    "user": device_user,
                    "device": device,
                    "created_ip": source_ip,
                    "user_agent": f"Vaulta seeded browser ({name})",
                    "last_seen_at": last_seen_at,
                    "revoked_at": None,
                },
            )
            LoginSession.objects.filter(pk=session.pk).update(
                created_at=last_seen_at - timedelta(hours=2)
            )

        attempt_rows = (
            (
                user,
                "192.0.2.44",
                "Firefox 128 · Linux",
                True,
                LoginAttempt.Reason.SUCCESS,
                1,
            ),
            (
                user,
                "198.51.100.27",
                "Chrome Mobile 126 · Android",
                True,
                LoginAttempt.Reason.SUCCESS,
                4,
            ),
            (
                user,
                "203.0.113.91",
                "Safari 17 · macOS",
                False,
                LoginAttempt.Reason.INVALID_PASSWORD,
                7,
            ),
            (
                finance_user,
                "192.0.2.83",
                "Edge 126 · Windows",
                True,
                LoginAttempt.Reason.SUCCESS,
                2,
            ),
            (
                nebula_admin,
                "203.0.113.18",
                "Chrome 127 · Linux",
                True,
                LoginAttempt.Reason.SUCCESS,
                2,
            ),
        )
        for attempt_user, source_ip, user_agent, successful, reason, days_ago in attempt_rows:
            attempt, _ = LoginAttempt.objects.update_or_create(
                user=attempt_user,
                source_ip=source_ip,
                user_agent=user_agent,
                reason=reason,
                defaults={
                    "entered_email": attempt_user.email,
                    "successful": successful,
                },
            )
            LoginAttempt.objects.filter(pk=attempt.pk).update(
                occurred_at=timezone.now() - timedelta(days=days_ago)
            )

        action = "criada" if created else "atualizada"
        self.stdout.write(self.style.SUCCESS(f"Conta demo {action}: demo@vaulta.local"))
        self.stdout.write(
            self.style.SUCCESS(
                "Dataset fictício pronto: "
                f"{user_model.objects.count()} usuários, "
                f"{Organization.objects.count()} organizações e "
                f"{Transaction.objects.count()} lançamentos."
            )
        )

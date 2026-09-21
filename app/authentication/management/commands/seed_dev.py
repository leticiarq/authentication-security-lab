from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from organizations.models import Membership, Organization


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

        action = "criada" if created else "atualizada"
        self.stdout.write(self.style.SUCCESS(f"Conta demo {action}: demo@vaulta.local"))

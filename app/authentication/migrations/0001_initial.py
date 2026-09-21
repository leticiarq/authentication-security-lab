import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="LoginAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entered_email", models.EmailField(max_length=254)),
                ("source_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=320)),
                ("successful", models.BooleanField(default=False)),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("success", "Autenticação concluída"),
                            ("unknown_account", "Conta não encontrada"),
                            ("invalid_password", "Senha inválida"),
                            ("inactive_account", "Conta inativa"),
                            ("unverified_account", "E-mail não verificado"),
                            ("client_locked", "Cliente temporariamente bloqueado"),
                        ],
                        max_length=32,
                    ),
                ),
                ("occurred_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="login_attempts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-occurred_at",)},
        )
    ]

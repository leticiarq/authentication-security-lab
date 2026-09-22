import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("organizations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FinancialAccount",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("type", models.CharField(choices=[("checking", "Conta corrente"), ("reserve", "Reserva"), ("receivables", "Recebíveis")], max_length=20)),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="financial_accounts", to="organizations.organization")),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("finance", "Financeiro"), ("security", "Segurança"), ("team", "Equipe")], max_length=16)),
                ("title", models.CharField(max_length=140)),
                ("body", models.TextField(max_length=500)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("description", models.CharField(max_length=180)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("direction", models.CharField(choices=[("income", "Entrada"), ("expense", "Saída")], max_length=12)),
                ("category", models.CharField(max_length=80)),
                ("occurred_on", models.DateField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="finance.financialaccount")),
            ],
            options={"ordering": ("-occurred_on", "-created_at")},
        ),
    ]

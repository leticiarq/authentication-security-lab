import uuid

from django.conf import settings
from django.db import models
from organizations.models import Organization


class FinancialAccount(models.Model):
    class Type(models.TextChoices):
        CHECKING = "checking", "Conta corrente"
        RESERVE = "reserve", "Reserva"
        RECEIVABLES = "receivables", "Recebíveis"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="financial_accounts",
    )
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=20, choices=Type.choices)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="BRL")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} — {self.organization}"


class Transaction(models.Model):
    class Direction(models.TextChoices):
        INCOME = "income", "Entrada"
        EXPENSE = "expense", "Saída"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        FinancialAccount,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    description = models.CharField(max_length=180)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    direction = models.CharField(max_length=12, choices=Direction.choices)
    category = models.CharField(max_length=80)
    occurred_on = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-occurred_on", "-created_at")

    def __str__(self):
        return self.description


class Notification(models.Model):
    class Kind(models.TextChoices):
        FINANCE = "finance", "Financeiro"
        SECURITY = "security", "Segurança"
        TEAM = "team", "Equipe"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    title = models.CharField(max_length=140)
    body = models.TextField(max_length=500)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

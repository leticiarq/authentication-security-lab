import uuid

from django.conf import settings
from django.db import models


class LoginAttempt(models.Model):
    class Reason(models.TextChoices):
        SUCCESS = "success", "Autenticação concluída"
        UNKNOWN_ACCOUNT = "unknown_account", "Conta não encontrada"
        INVALID_PASSWORD = "invalid_password", "Senha inválida"
        INACTIVE_ACCOUNT = "inactive_account", "Conta inativa"
        UNVERIFIED_ACCOUNT = "unverified_account", "E-mail não verificado"
        CLIENT_LOCKED = "client_locked", "Cliente temporariamente bloqueado"

    entered_email = models.EmailField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_attempts",
    )
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=320, blank=True)
    successful = models.BooleanField(default=False)
    reason = models.CharField(max_length=32, choices=Reason.choices)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-occurred_at",)

    def __str__(self):
        return f"{self.entered_email} — {self.reason}"


class PasswordResetRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_requests",
    )
    token = models.CharField(max_length=12, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    requested_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def is_used(self):
        return self.used_at is not None

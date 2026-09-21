import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def invitation_token():
    return secrets.token_urlsafe(24)


def invitation_expiry():
    return timezone.now() + timedelta(days=7)


class Organization(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        SUSPENDED = "suspended", "Suspensa"

    class Plan(models.TextChoices):
        ESSENTIAL = "essential", "Essencial"
        GROWTH = "growth", "Crescimento"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    plan = models.CharField(max_length=16, choices=Plan.choices, default=Plan.ESSENTIAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", "Membro"
        ADMIN = "admin", "Administrador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("user__full_name",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "organization"),
                name="unique_organization_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} em {self.organization}"


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=16,
        choices=Membership.Role.choices,
        default=Membership.Role.MEMBER,
    )
    token = models.CharField(max_length=64, unique=True, default=invitation_token)
    expires_at = models.DateTimeField(default=invitation_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="organization_invitations_sent",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def is_available(self):
        return self.accepted_at is None and self.expires_at > timezone.now()

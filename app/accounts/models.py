import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        REGULAR = "regular", "Usuário"
        SYSTEM_ADMIN = "system_admin", "Administrador do sistema"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    first_name = None
    last_name = None
    email = models.EmailField("e-mail", unique=True)
    full_name = models.CharField("nome", max_length=160)
    role = models.CharField(max_length=24, choices=Role.choices, default=Role.REGULAR)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email.split("@", 1)[0]

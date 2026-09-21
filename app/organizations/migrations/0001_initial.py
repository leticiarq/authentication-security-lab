import uuid

import django.db.models.deletion
import organizations.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=140)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                (
                    "status",
                    models.CharField(choices=[("active", "Ativa"), ("suspended", "Suspensa")], default="active", max_length=16),
                ),
                (
                    "plan",
                    models.CharField(choices=[("essential", "Essencial"), ("growth", "Crescimento")], default="essential", max_length=16),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Invitation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(max_length=254)),
                (
                    "role",
                    models.CharField(choices=[("member", "Membro"), ("admin", "Administrador")], default="member", max_length=16),
                ),
                ("token", models.CharField(default=organizations.models.invitation_token, max_length=64, unique=True)),
                ("expires_at", models.DateTimeField(default=organizations.models.invitation_expiry)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "invited_by",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_invitations_sent", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "organization",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="organizations.organization"),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "role",
                    models.CharField(choices=[("member", "Membro"), ("admin", "Administrador")], default="member", max_length=16),
                ),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                (
                    "organization",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="organizations.organization"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ("user__full_name",)},
        ),
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.UniqueConstraint(fields=("user", "organization"), name="unique_organization_membership"),
        ),
    ]

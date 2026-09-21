import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_passwordresetrequest"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Device",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("fingerprint", models.CharField(max_length=64)),
                ("last_seen_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("trusted_until", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ("-last_seen_at",)},
        ),
        migrations.CreateModel(
            name="LoginSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("django_session_key", models.CharField(max_length=40, unique=True)),
                ("created_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=320)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "device",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="login_sessions", to="authentication.device"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="login_sessions", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ("-last_seen_at",)},
        ),
        migrations.AddConstraint(
            model_name="device",
            constraint=models.UniqueConstraint(fields=("user", "fingerprint"), name="unique_user_device_fingerprint"),
        ),
    ]

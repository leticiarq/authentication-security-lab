import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("locale", models.CharField(default="pt-BR", max_length=12)),
                ("timezone", models.CharField(default="America/Recife", max_length=64)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("notify_financial", models.BooleanField(default=True)),
                ("notify_security", models.BooleanField(default=True)),
                ("notify_team", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="preferences", to=settings.AUTH_USER_MODEL)),
            ],
        )
    ]

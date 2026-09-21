import os

from .base import *  # noqa: F403
from .base import env_bool, env_list


DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "vaulta"),
        "USER": os.getenv("POSTGRES_USER", "vaulta"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "vaulta-local-only"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# Phase 1 intentionally keeps Django's secure defaults. Deliberate lab overrides are
# introduced only with the feature that requires them and are catalogued in the threat model.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

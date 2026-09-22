"""PostgreSQL-backed settings used by the release validation suite."""

from .development import *  # noqa: F403

SECRET_KEY = "test-only-postgres-secret-key"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

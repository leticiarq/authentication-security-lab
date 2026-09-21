import ipaddress
from dataclasses import dataclass

from django.contrib.auth import get_user_model

from .models import LoginAttempt


User = get_user_model()


@dataclass(frozen=True)
class AuthenticationResult:
    user: User | None
    reason: str

    @property
    def succeeded(self) -> bool:
        return self.user is not None and self.reason == LoginAttempt.Reason.SUCCESS


def check_credentials(email: str, password: str) -> AuthenticationResult:
    """Check first-factor credentials for the local lab.

    INTENTIONAL LAB BEHAVIOR (AUTH-01/AUTH-02): an unknown account returns
    immediately, while an existing account runs the password hasher. The caller
    also maps the two failures to different form fields. Production code should
    use Django's authentication backend and a uniform public response.
    """
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return AuthenticationResult(None, LoginAttempt.Reason.UNKNOWN_ACCOUNT)

    if not user.check_password(password):
        return AuthenticationResult(user, LoginAttempt.Reason.INVALID_PASSWORD)
    if not user.is_active:
        return AuthenticationResult(user, LoginAttempt.Reason.INACTIVE_ACCOUNT)
    if not user.email_verified:
        return AuthenticationResult(user, LoginAttempt.Reason.UNVERIFIED_ACCOUNT)
    return AuthenticationResult(user, LoginAttempt.Reason.SUCCESS)


def client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    value = forwarded_for.split(",", 1)[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def record_attempt(request, email: str, result: AuthenticationResult) -> None:
    LoginAttempt.objects.create(
        entered_email=email,
        user=result.user,
        source_ip=client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:320],
        successful=result.succeeded,
        reason=result.reason,
    )

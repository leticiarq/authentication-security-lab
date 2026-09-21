import hashlib
import ipaddress
import random
import time
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Device, LoginAttempt, LoginSession, PasswordResetRequest


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


def generate_password_reset_token(user, timestamp: float | None = None) -> str:
    """Generate the deliberately weak token used by the vulnerable release.

    INTENTIONAL LAB BEHAVIOR (AUTH-10): random.Random is deterministic and not
    suitable for credentials. The seed combines a discoverable identifier with
    a one-minute time bucket, and the output space is only six decimal digits.
    Production recovery tokens must use a cryptographically secure generator.
    """
    current_time = time.time() if timestamp is None else timestamp
    minute_bucket = int(current_time // 60)
    generator = random.Random(f"{user.pk}:{minute_bucket}")
    return str(generator.randrange(100000, 1000000))


def create_password_reset(request, user) -> PasswordResetRequest:
    reset_request = PasswordResetRequest.objects.create(
        user=user,
        token=generate_password_reset_token(user),
        expires_at=timezone.now() + timedelta(minutes=15),
        requested_ip=client_ip(request),
    )
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    path = reverse(
        "authentication:password-reset",
        kwargs={"uidb64": uidb64, "token": reset_request.token},
    )
    body = render_to_string(
        "authentication/emails/password_reset.txt",
        {"user": user, "reset_url": request.build_absolute_uri(path)},
    )
    send_mail(
        subject="Redefina sua senha da Vaulta",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    return reset_request


def _device_name(user_agent: str) -> str:
    value = user_agent.lower()
    if "firefox" in value:
        browser = "Firefox"
    elif "edg/" in value:
        browser = "Edge"
    elif "chrome" in value:
        browser = "Chrome"
    elif "safari" in value:
        browser = "Safari"
    else:
        browser = "Navegador"

    if "android" in value:
        platform = "Android"
    elif "iphone" in value or "ipad" in value:
        platform = "iOS"
    elif "windows" in value:
        platform = "Windows"
    elif "mac os" in value:
        platform = "macOS"
    elif "linux" in value:
        platform = "Linux"
    else:
        platform = "dispositivo desconhecido"
    return f"{browser} em {platform}"


def register_authenticated_session(request, user) -> LoginSession:
    if not request.session.session_key:
        request.session.save()
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:320]
    ip = client_ip(request)
    fingerprint_source = f"{user_agent}|{ip or ''}"
    fingerprint = hashlib.sha256(fingerprint_source.encode()).hexdigest()
    device, _ = Device.objects.update_or_create(
        user=user,
        fingerprint=fingerprint,
        defaults={
            "name": _device_name(user_agent),
            "last_seen_at": timezone.now(),
            "revoked_at": None,
        },
    )
    session, _ = LoginSession.objects.update_or_create(
        django_session_key=request.session.session_key,
        defaults={
            "user": user,
            "device": device,
            "created_ip": ip,
            "user_agent": user_agent,
            "last_seen_at": timezone.now(),
            "revoked_at": None,
        },
    )
    return session

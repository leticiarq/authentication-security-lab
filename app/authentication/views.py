import time
from datetime import timedelta

from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    get_user_model,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)
from django.views.decorators.http import require_POST
from finance.models import Transaction
from finance.services import dashboard_summary
from organizations.models import Membership

from .forms import (
    AssistedRecoveryForm,
    LoginForm,
    MFACodeForm,
    MFASetupForm,
    PasswordRecoveryRequestForm,
    SetNewPasswordForm,
)
from .middleware import REMEMBER_COOKIE_NAME
from .models import LoginAttempt, LoginSession, MFAProfile, PasswordResetRequest
from .services import (
    AuthenticationResult,
    check_credentials,
    consume_recovery_code,
    create_password_reset,
    generate_recovery_codes,
    record_attempt,
    register_authenticated_session,
    trusted_device_from_request,
)
from .totp import generate_secret, provisioning_uri, verify_code

FAILURE_LIMIT = 5
LOCK_SECONDS = 60
REMEMBER_SECONDS = 60 * 60 * 24 * 30
User = get_user_model()


def _safe_next_url(request) -> str:
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return reverse("authentication:dashboard")


def _client_lock_remaining(request) -> int:
    locked_until = request.session.get("login_locked_until", 0)
    return max(0, int(locked_until - time.time()))


def _register_failure(request) -> None:
    # INTENTIONAL LAB BEHAVIOR (AUTH-04): the attempt counter lives in the
    # anonymous browser session. Starting a new session discards the protection.
    failures = request.session.get("login_failures", 0) + 1
    request.session["login_failures"] = failures
    if failures >= FAILURE_LIMIT:
        request.session["login_locked_until"] = time.time() + LOCK_SECONDS


def login_view(request):
    if request.user.is_authenticated:
        return redirect("authentication:dashboard")

    next_url = _safe_next_url(request)
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if _client_lock_remaining(request):
                result = AuthenticationResult(None, LoginAttempt.Reason.CLIENT_LOCKED)
                record_attempt(request, email, result)
                form.add_error(None, "Muitas tentativas. Aguarde um minuto e tente novamente.")
            else:
                result = check_credentials(email, form.cleaned_data["password"])
                record_attempt(request, email, result)
                if result.succeeded:
                    request.session.pop("login_failures", None)
                    request.session.pop("login_locked_until", None)
                    mfa_profile = MFAProfile.objects.filter(
                        user=result.user,
                        enabled_at__isnull=False,
                    ).first()
                    if mfa_profile and not trusted_device_from_request(request, result.user):
                        request.session["pending_auth_user_id"] = str(result.user.pk)
                        request.session["password_verified"] = True
                        request.session["pending_remember_me"] = form.cleaned_data["remember_me"]
                        request.session["pending_next"] = next_url
                        return redirect("authentication:mfa-challenge")
                    login(
                        request,
                        result.user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )
                    register_authenticated_session(request, result.user)
                    response = redirect(next_url)
                    if form.cleaned_data["remember_me"]:
                        request.session.set_expiry(REMEMBER_SECONDS)
                        response.set_cookie(
                            REMEMBER_COOKIE_NAME,
                            str(result.user.pk),
                            max_age=REMEMBER_SECONDS,
                            httponly=True,
                            samesite="Lax",
                        )
                    else:
                        request.session.set_expiry(0)
                    return response

                _register_failure(request)
                if result.reason == LoginAttempt.Reason.UNKNOWN_ACCOUNT:
                    form.add_error("email", "Não foi possível localizar o acesso informado.")
                elif result.reason == LoginAttempt.Reason.INVALID_PASSWORD:
                    form.add_error("password", "Não foi possível validar o acesso informado.")
                elif result.reason == LoginAttempt.Reason.UNVERIFIED_ACCOUNT:
                    form.add_error(None, "Confirme seu e-mail antes de acessar a conta.")
                else:
                    form.add_error(None, "Esta conta não está disponível no momento.")
    else:
        form = LoginForm()

    return render(
        request,
        "authentication/login.html",
        {"form": form, "next": next_url},
    )


@require_POST
def logout_view(request):
    if request.user.is_authenticated and request.session.session_key:
        LoginSession.objects.filter(
            user=request.user,
            django_session_key=request.session.session_key,
        ).update(revoked_at=timezone.now())
    logout(request)
    response = redirect("home")
    response.delete_cookie(REMEMBER_COOKIE_NAME)
    return response


@login_required
def dashboard(request):
    return render(request, "authentication/dashboard.html", dashboard_summary(request.user))


def _complete_multistage_login(request, user):
    """Complete the MFA transition while preserving the pre-auth session.

    INTENTIONAL LAB BEHAVIOR (AUTH-08): Django's login() rotates the session
    key. This compatibility helper writes the authentication keys directly so
    wizard state survives, leaving the identifier fixed across authentication.
    """
    request.session[SESSION_KEY] = str(user.pk)
    request.session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    request.user = user


def mfa_challenge(request):
    user_id = request.session.get("pending_auth_user_id")
    if not user_id or not request.session.get("password_verified"):
        return redirect("authentication:login")
    user = get_object_or_404(User, pk=user_id, is_active=True)
    profile = get_object_or_404(MFAProfile, user=user, enabled_at__isnull=False)

    if request.method == "POST":
        form = MFACodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            if verify_code(profile.secret, code) or consume_recovery_code(profile, code):
                next_url = request.session.get("pending_next", reverse("authentication:dashboard"))
                remember_me = request.session.get("pending_remember_me", False)
                for key in (
                    "pending_auth_user_id",
                    "password_verified",
                    "pending_remember_me",
                    "pending_next",
                ):
                    request.session.pop(key, None)
                _complete_multistage_login(request, user)
                if remember_me:
                    request.session.set_expiry(REMEMBER_SECONDS)
                else:
                    request.session.set_expiry(0)
                login_session = register_authenticated_session(request, user)
                response = redirect(next_url)
                if form.cleaned_data["trust_device"] and login_session.device:
                    login_session.device.trusted_until = timezone.now() + timedelta(days=30)
                    login_session.device.save(update_fields=["trusted_until"])
                    response.set_cookie(
                        "vaulta_trusted_device",
                        str(login_session.device_id),
                        max_age=REMEMBER_SECONDS,
                        httponly=True,
                        samesite="Lax",
                    )
                return response
            form.add_error("code", "O código informado não é válido.")
    else:
        form = MFACodeForm()
    return render(request, "authentication/mfa/challenge.html", {"form": form})


@login_required
def security_settings(request):
    profile = MFAProfile.objects.filter(user=request.user).first()
    recovery_codes = request.session.pop("new_recovery_codes", None)
    return render(
        request,
        "authentication/mfa/security_settings.html",
        {"mfa_profile": profile, "recovery_codes": recovery_codes},
    )


@login_required
def mfa_setup(request):
    profile, _ = MFAProfile.objects.get_or_create(
        user=request.user,
        defaults={"secret": generate_secret()},
    )
    if profile.is_enabled:
        return redirect("authentication:security-settings")
    if request.method == "POST":
        form = MFASetupForm(request.POST)
        if form.is_valid() and verify_code(profile.secret, form.cleaned_data["code"]):
            profile.enabled_at = timezone.now()
            profile.save(update_fields=["enabled_at"])
            request.session["new_recovery_codes"] = generate_recovery_codes(profile)
            return redirect("authentication:security-settings")
        if form.is_valid():
            form.add_error("code", "O código informado não é válido.")
    else:
        form = MFASetupForm()
    return render(
        request,
        "authentication/mfa/setup.html",
        {
            "form": form,
            "secret": profile.secret,
            "provisioning_uri": provisioning_uri(profile.secret, request.user.email),
        },
    )


@require_POST
@login_required
def regenerate_recovery_codes(request):
    profile = get_object_or_404(MFAProfile, user=request.user, enabled_at__isnull=False)
    code = request.POST.get("code", "")
    if not verify_code(profile.secret, code):
        return redirect("authentication:security-settings")
    request.session["new_recovery_codes"] = generate_recovery_codes(profile)
    return redirect("authentication:security-settings")


@require_POST
@login_required
def disable_mfa(request):
    profile = get_object_or_404(MFAProfile, user=request.user, enabled_at__isnull=False)
    if verify_code(profile.secret, request.POST.get("code", "")):
        profile.delete()
        request.user.devices.update(trusted_until=None)
    return redirect("authentication:security-settings")


@login_required
def session_management(request):
    sessions = request.user.login_sessions.select_related("device").filter(revoked_at__isnull=True)
    devices = request.user.devices.filter(revoked_at__isnull=True)
    return render(
        request,
        "authentication/security/sessions.html",
        {
            "sessions": sessions,
            "devices": devices,
            "current_session_key": request.session.session_key,
        },
    )


@login_required
def login_history(request):
    attempts = request.user.login_attempts.all()[:50]
    return render(request, "authentication/security/login_history.html", {"attempts": attempts})


@require_POST
@login_required
def revoke_session(request, session_id):
    session = get_object_or_404(LoginSession, pk=session_id, user=request.user)

    # INTENTIONAL LAB BEHAVIOR (AUTH-07): revocation only updates Vaulta's
    # inventory record. The corresponding django_session row is not deleted,
    # and no middleware enforces revoked_at, so that browser remains logged in.
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])
    return redirect("authentication:sessions")


@require_POST
@login_required
def revoke_other_sessions(request):
    request.user.login_sessions.exclude(
        django_session_key=request.session.session_key
    ).filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
    return redirect("authentication:sessions")


def password_recovery(request):
    if request.method == "POST":
        form = PasswordRecoveryRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email=email, is_active=True).first()
            if user:
                create_password_reset(request, user)
                request.session["recovery_email"] = email
                return redirect("authentication:password-recovery-sent")

            # INTENTIONAL LAB BEHAVIOR (AUTH-01): the recovery flow renders a
            # field-specific error for an unknown account instead of returning
            # the same acknowledgement used for an existing account.
            form.add_error("email", "Não foi possível localizar o acesso informado.")
    else:
        form = PasswordRecoveryRequestForm()
    return render(request, "authentication/password_recovery.html", {"form": form})


def password_recovery_sent(request):
    email = request.session.get("recovery_email")
    if not email:
        return redirect("authentication:password-recovery")
    return render(request, "authentication/password_recovery_sent.html", {"email": email})


def assisted_password_recovery(request):
    if request.method == "POST":
        form = AssistedRecoveryForm(request.POST)
        if form.is_valid():
            membership = (
                Membership.objects.select_related("user", "organization")
                .filter(
                    user__email=form.cleaned_data["email"],
                    organization__name__iexact=form.cleaned_data["organization_name"],
                )
                .first()
            )
            latest_transaction = None
            if membership:
                latest_transaction = (
                    Transaction.objects.filter(account__organization=membership.organization)
                    .order_by("-occurred_on", "-created_at")
                    .first()
                )
            if (
                latest_transaction
                and latest_transaction.amount == form.cleaned_data["latest_transaction_amount"]
            ):
                # INTENTIONAL LAB BEHAVIOR (AUTH-09): organization name and a
                # transaction value shared with every tenant member are treated
                # as sufficient identity proof. The reset URL is handed directly
                # to the requester instead of requiring mailbox access.
                reset_request = create_password_reset(request, membership.user)
                uidb64 = urlsafe_base64_encode(force_bytes(membership.user.pk))
                return redirect(
                    "authentication:password-reset",
                    uidb64=uidb64,
                    token=reset_request.token,
                )
            form.add_error(None, "Não foi possível validar os dados informados.")
    else:
        form = AssistedRecoveryForm()
    return render(request, "authentication/assisted_recovery.html", {"form": form})


def _password_reset_request(uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
    except (TypeError, ValueError, OverflowError):
        return None
    return (
        PasswordResetRequest.objects.select_related("user")
        .filter(
            user_id=user_id,
            token=token,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )


def password_reset(request, uidb64, token):
    reset_request = _password_reset_request(uidb64, token)
    if not reset_request:
        return render(request, "authentication/password_reset_invalid.html", status=400)

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                current_reset = PasswordResetRequest.objects.select_for_update().get(
                    pk=reset_request.pk
                )
                if current_reset.used_at or current_reset.expires_at <= timezone.now():
                    return render(
                        request,
                        "authentication/password_reset_invalid.html",
                        status=400,
                    )
                current_reset.user.set_password(form.cleaned_data["password"])
                current_reset.user.save(update_fields=["password", "updated_at"])
                current_reset.used_at = timezone.now()
                current_reset.save(update_fields=["used_at"])
            return redirect("authentication:password-reset-complete")
    else:
        form = SetNewPasswordForm()

    return render(request, "authentication/password_reset.html", {"form": form})


def password_reset_complete(request):
    return render(request, "authentication/password_reset_complete.html")

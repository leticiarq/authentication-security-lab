import time

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm
from .middleware import REMEMBER_COOKIE_NAME
from .models import LoginAttempt
from .services import AuthenticationResult, check_credentials, record_attempt


FAILURE_LIMIT = 5
LOCK_SECONDS = 60
REMEMBER_SECONDS = 60 * 60 * 24 * 30


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
                    login(
                        request,
                        result.user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )
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
    logout(request)
    response = redirect("home")
    response.delete_cookie(REMEMBER_COOKIE_NAME)
    return response


@login_required
def dashboard(request):
    return render(request, "authentication/dashboard.html")

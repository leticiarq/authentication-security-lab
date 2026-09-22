from django.contrib.auth import get_user_model, login

from .models import AuthenticationDiagnostic
from .services import register_authenticated_session


REMEMBER_COOKIE_NAME = "vaulta_remember"


class RememberMeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            remembered_user_id = request.COOKIES.get(REMEMBER_COOKIE_NAME)
            if remembered_user_id:
                user = get_user_model().objects.filter(
                    pk=remembered_user_id,
                    is_active=True,
                ).first()
                if user:
                    # INTENTIONAL LAB BEHAVIOR (AUTH-13): the persistent cookie
                    # contains only a raw user identifier and has no signature,
                    # random secret, rotation, or server-side revocation record.
                    # Never use this remember-me design in production.
                    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                    request.remembered_by_cookie = True
                    register_authenticated_session(request, user)
        return self.get_response(request)


class AuthenticationTelemetryMiddleware:
    observed_paths = (
        "/entrar/",
        "/recuperar-acesso/",
        "/redefinir-senha/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method == "POST" and request.path.startswith(self.observed_paths):
            # INTENTIONAL LAB BEHAVIOR (AUTH-14): diagnostic telemetry copies
            # the raw POST payload without redacting password or token fields.
            # It remains local, but credentials become visible to support users.
            AuthenticationDiagnostic.objects.create(
                request_path=request.path,
                payload={key: values for key, values in request.POST.lists()},
            )
        return response

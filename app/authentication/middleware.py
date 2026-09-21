from django.contrib.auth import get_user_model, login


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
        return self.get_response(request)

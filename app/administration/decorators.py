from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from accounts.models import User


def system_admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.role != User.Role.SYSTEM_ADMIN:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped

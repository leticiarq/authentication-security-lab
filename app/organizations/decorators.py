from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Membership


def organization_member_required(admin=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            membership = (
                Membership.objects.select_related("organization")
                .filter(user=request.user, organization__status="active")
                .first()
            )
            if not membership or (admin and membership.role != Membership.Role.ADMIN):
                raise PermissionDenied
            request.membership = membership
            request.organization = membership.organization
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator

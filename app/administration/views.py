from authentication.models import AuthenticationDiagnostic, LoginAttempt
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from organizations.models import Organization

from .decorators import system_admin_required

User = get_user_model()


@system_admin_required
def dashboard(request):
    return render(
        request,
        "administration/dashboard.html",
        {
            "user_count": User.objects.count(),
            "organization_count": Organization.objects.count(),
            "failed_login_count": LoginAttempt.objects.filter(successful=False).count(),
            "diagnostic_count": AuthenticationDiagnostic.objects.count(),
        },
    )


@system_admin_required
def users(request):
    return render(
        request,
        "administration/users.html",
        {"managed_users": User.objects.order_by("full_name", "email")},
    )


@require_POST
@system_admin_required
def toggle_user_status(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        raise PermissionDenied
    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])
    return redirect("administration:users")


@system_admin_required
def organizations(request):
    organizations_list = Organization.objects.prefetch_related("memberships").all()
    return render(
        request,
        "administration/organizations.html",
        {"managed_organizations": organizations_list},
    )


@system_admin_required
def diagnostics(request):
    return render(
        request,
        "administration/diagnostics.html",
        {"diagnostics": AuthenticationDiagnostic.objects.all()[:100]},
    )

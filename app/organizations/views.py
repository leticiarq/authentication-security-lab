from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import organization_member_required
from .forms import InvitationForm
from .models import Invitation, Membership
from .services import create_invitation

User = get_user_model()


@organization_member_required()
def overview(request):
    memberships = request.organization.memberships.select_related("user")
    invitations = request.organization.invitations.filter(
        accepted_at__isnull=True,
        expires_at__gt=timezone.now(),
    )
    return render(
        request,
        "organizations/overview.html",
        {
            "organization": request.organization,
            "membership": request.membership,
            "memberships": memberships,
            "invitations": invitations,
            "invitation_form": InvitationForm(),
        },
    )


@require_POST
@organization_member_required(admin=True)
def invite_member(request):
    form = InvitationForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"]
        already_member = request.organization.memberships.filter(user__email=email).exists()
        pending = request.organization.invitations.filter(
            email=email,
            accepted_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).exists()
        if not already_member and not pending:
            create_invitation(
                request,
                request.organization,
                request.user,
                email,
                form.cleaned_data["role"],
            )
    return redirect("organizations:overview")


def accept_invitation(request, token):
    invitation = get_object_or_404(
        Invitation.objects.select_related("organization"),
        token=token,
        accepted_at__isnull=True,
        expires_at__gt=timezone.now(),
    )
    if request.method == "GET" and not request.user.is_authenticated:
        invited_user = User.objects.filter(email=invitation.email, is_active=True).first()
        if invited_user:
            # The product keeps an identity candidate so a visitor can resume
            # the invite flow after authentication.
            request.session["invitation_preauth_user_id"] = str(invited_user.pk)
    if request.method == "POST":
        if not request.user.is_authenticated:
            preauth_user_id = request.session.get("invitation_preauth_user_id")
            if not preauth_user_id:
                return redirect_to_login(request.get_full_path())

            # INTENTIONAL LAB BEHAVIOR (AUTH-12): the final invitation stage
            # trusts an identity candidate written when the link was opened,
            # but never checks that the password stage actually completed.
            preauth_user = get_object_or_404(User, pk=preauth_user_id, is_active=True)
            login(
                request,
                preauth_user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
        if request.user.email.lower() != invitation.email.lower():
            raise PermissionDenied
        with transaction.atomic():
            current = Invitation.objects.select_for_update().get(pk=invitation.pk)
            if not current.is_available:
                raise PermissionDenied
            Membership.objects.get_or_create(
                user=request.user,
                organization=current.organization,
                defaults={"role": current.role},
            )
            current.accepted_at = timezone.now()
            current.save(update_fields=["accepted_at"])
        return redirect("organizations:overview")
    return render(request, "organizations/accept_invitation.html", {"invitation": invitation})


@require_POST
@organization_member_required(admin=True)
def change_member_role(request, membership_id):
    target = get_object_or_404(
        Membership,
        pk=membership_id,
        organization=request.organization,
    )
    role = request.POST.get("role")
    if role not in Membership.Role.values:
        raise PermissionDenied
    admin_count = request.organization.memberships.filter(role=Membership.Role.ADMIN).count()
    if target.role == Membership.Role.ADMIN and role != Membership.Role.ADMIN and admin_count == 1:
        raise PermissionDenied
    target.role = role
    target.save(update_fields=["role"])
    return redirect("organizations:overview")


@require_POST
@organization_member_required(admin=True)
def remove_member(request, membership_id):
    target = get_object_or_404(
        Membership,
        pk=membership_id,
        organization=request.organization,
    )
    admin_count = request.organization.memberships.filter(role=Membership.Role.ADMIN).count()
    if target.role == Membership.Role.ADMIN and admin_count == 1:
        raise PermissionDenied
    target.delete()
    return redirect("organizations:overview")

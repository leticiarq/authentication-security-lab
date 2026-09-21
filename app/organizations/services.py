from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Invitation


def create_invitation(request, organization, invited_by, email, role):
    invitation = Invitation.objects.create(
        organization=organization,
        invited_by=invited_by,
        email=email,
        role=role,
    )
    path = reverse("organizations:accept-invitation", kwargs={"token": invitation.token})
    body = render_to_string(
        "organizations/emails/invitation.txt",
        {
            "invitation": invitation,
            "invitation_url": request.build_absolute_uri(path),
        },
    )
    send_mail(
        subject=f"Você foi convidado para {organization.name} na Vaulta",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
    return invitation

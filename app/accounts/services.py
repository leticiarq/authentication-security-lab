from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_email_verification_url(request, user) -> str:
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse(
        "accounts:verify-email",
        kwargs={"uidb64": uidb64, "token": token},
    )
    return request.build_absolute_uri(path)


def send_verification_email(request, user) -> None:
    context = {
        "user": user,
        "verification_url": build_email_verification_url(request, user),
    }
    body = render_to_string("accounts/emails/verify_email.txt", context)
    send_mail(
        subject="Confirme seu e-mail na Vaulta",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

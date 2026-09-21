from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_POST

from .forms import RegistrationForm
from .services import send_verification_email


User = get_user_model()


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            request.session["registration_email"] = user.email
            return redirect("accounts:registration-complete")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def registration_complete(request):
    email = request.session.get("registration_email")
    if not email:
        return redirect("accounts:register")
    return render(request, "accounts/registration_complete.html", {"email": email})


@require_POST
def resend_verification(request):
    email = request.session.get("registration_email")
    if not email:
        return redirect("accounts:register")

    user = User.objects.filter(email=email, email_verified=False).first()
    if user:
        send_verification_email(request, user)
    return redirect("accounts:registration-complete")


def verify_email(request, uidb64, token):
    user = None
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        pass

    valid = bool(user and default_token_generator.check_token(user, token))
    if valid and not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified", "updated_at"])

    return render(
        request,
        "accounts/verification_result.html",
        {"verification_succeeded": valid},
        status=200 if valid else 400,
    )

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("cadastro/", views.register, name="register"),
    path("cadastro/concluido/", views.registration_complete, name="registration-complete"),
    path("cadastro/reenviar/", views.resend_verification, name="resend-verification"),
    path(
        "verificar-email/<uidb64>/<token>/",
        views.verify_email,
        name="verify-email",
    ),
]

from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    path("entrar/", views.login_view, name="login"),
    path("sair/", views.logout_view, name="logout"),
    path("recuperar-acesso/", views.password_recovery, name="password-recovery"),
    path(
        "recuperar-acesso/enviado/",
        views.password_recovery_sent,
        name="password-recovery-sent",
    ),
    path(
        "redefinir-senha/<uidb64>/<token>/",
        views.password_reset,
        name="password-reset",
    ),
    path(
        "redefinir-senha/concluido/",
        views.password_reset_complete,
        name="password-reset-complete",
    ),
    path("app/", views.dashboard, name="dashboard"),
    path("app/seguranca/sessoes/", views.session_management, name="sessions"),
    path("app/seguranca/acessos/", views.login_history, name="login-history"),
    path(
        "app/seguranca/sessoes/<uuid:session_id>/revogar/",
        views.revoke_session,
        name="revoke-session",
    ),
    path(
        "app/seguranca/sessoes/revogar-outras/",
        views.revoke_other_sessions,
        name="revoke-other-sessions",
    ),
]

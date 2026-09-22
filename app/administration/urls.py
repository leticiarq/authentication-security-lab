from django.urls import path

from . import views

app_name = "administration"

urlpatterns = [
    path("controle/", views.dashboard, name="dashboard"),
    path("controle/usuarios/", views.users, name="users"),
    path(
        "controle/usuarios/<uuid:user_id>/status/",
        views.toggle_user_status,
        name="toggle-user-status",
    ),
    path("controle/organizacoes/", views.organizations, name="organizations"),
    path("controle/suporte/diagnostico/", views.diagnostics, name="diagnostics"),
]

from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    path("entrar/", views.login_view, name="login"),
    path("sair/", views.logout_view, name="logout"),
    path("app/", views.dashboard, name="dashboard"),
]

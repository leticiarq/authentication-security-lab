from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("sobre/", views.about, name="about"),
    path("ajuda/", views.help_center, name="help"),
    path("termos/", views.terms, name="terms"),
    path("health/", views.health, name="health"),
]

from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("app/organizacao/", views.overview, name="overview"),
    path("app/organizacao/convites/", views.invite_member, name="invite-member"),
    path(
        "app/organizacao/membros/<uuid:membership_id>/papel/",
        views.change_member_role,
        name="change-member-role",
    ),
    path(
        "app/organizacao/membros/<uuid:membership_id>/remover/",
        views.remove_member,
        name="remove-member",
    ),
    path("convites/<str:token>/", views.accept_invitation, name="accept-invitation"),
]

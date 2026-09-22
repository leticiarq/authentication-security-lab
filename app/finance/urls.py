from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("app/notificacoes/", views.notifications, name="notifications"),
    path("app/notificacoes/marcar-lidas/", views.mark_notifications_read, name="mark-read"),
    path(
        "api/v1/dashboard/summary/",
        views.DashboardSummaryAPI.as_view(),
        name="dashboard-summary",
    ),
]

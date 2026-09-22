from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("authentication.urls")),
    path("", include("organizations.urls")),
    path("", include("finance.urls")),
    path("", include("core.urls")),
]

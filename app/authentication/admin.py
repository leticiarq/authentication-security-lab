from django.contrib import admin

from .models import LoginAttempt


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("entered_email", "successful", "reason", "source_ip", "occurred_at")
    list_filter = ("successful", "reason", "occurred_at")
    search_fields = ("entered_email", "source_ip")
    readonly_fields = (
        "entered_email",
        "user",
        "source_ip",
        "user_agent",
        "successful",
        "reason",
        "occurred_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

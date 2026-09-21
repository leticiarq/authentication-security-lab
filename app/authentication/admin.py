from django.contrib import admin

from .models import LoginAttempt, PasswordResetRequest


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


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "used_at", "requested_ip")
    list_filter = ("created_at", "used_at")
    search_fields = ("user__email",)
    exclude = ("token",)
    readonly_fields = ("user", "expires_at", "used_at", "requested_ip", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

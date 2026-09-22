from django.contrib import admin

from .models import FinancialAccount, Notification, Transaction


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "type", "balance", "currency")
    list_filter = ("type", "currency")
    search_fields = ("name", "organization__name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("description", "account", "direction", "amount", "occurred_on")
    list_filter = ("direction", "category", "occurred_on")
    search_fields = ("description", "account__organization__name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "kind", "created_at", "read_at")
    list_filter = ("kind", "created_at", "read_at")
    search_fields = ("title", "user__email")

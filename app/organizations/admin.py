from django.contrib import admin

from .models import Invitation, Membership, Organization


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "plan", "status", "created_at")
    list_filter = ("plan", "status")
    search_fields = ("name", "slug")
    inlines = (MembershipInline,)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "organization", "role", "created_at", "accepted_at")
    list_filter = ("role", "created_at", "accepted_at")
    search_fields = ("email", "organization__name")
    readonly_fields = ("token", "created_at", "accepted_at")

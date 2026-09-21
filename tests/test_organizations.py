from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from organizations.models import Invitation, Membership, Organization


class OrganizationAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@aurora.local",
            password="admin-password",
            full_name="Admin Aurora",
            email_verified=True,
        )
        self.member = user_model.objects.create_user(
            email="member@aurora.local",
            password="member-password",
            full_name="Member Aurora",
            email_verified=True,
        )
        self.outsider = user_model.objects.create_user(
            email="outsider@example.local",
            password="outsider-password",
            full_name="Outside User",
            email_verified=True,
        )
        self.organization = Organization.objects.create(name="Aurora", slug="aurora")
        self.admin_membership = Membership.objects.create(
            user=self.admin,
            organization=self.organization,
            role=Membership.Role.ADMIN,
        )
        self.member_membership = Membership.objects.create(
            user=self.member,
            organization=self.organization,
            role=Membership.Role.MEMBER,
        )

    def test_member_can_view_organization(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse("organizations:overview"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aurora")
        self.assertContains(response, self.admin.email)

    def test_outsider_is_forbidden(self):
        self.client.force_login(self.outsider)

        self.assertEqual(self.client.get(reverse("organizations:overview")).status_code, 403)

    def test_regular_member_cannot_invite(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("organizations:invite-member"),
            {"email": "new@example.local", "role": Membership.Role.MEMBER},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Invitation.objects.exists())

    def test_membership_is_unique_inside_organization(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.create(user=self.member, organization=self.organization)

    def test_last_admin_cannot_be_removed_or_demoted(self):
        self.client.force_login(self.admin)

        remove = self.client.post(
            reverse("organizations:remove-member", args=[self.admin_membership.id])
        )
        demote = self.client.post(
            reverse("organizations:change-member-role", args=[self.admin_membership.id]),
            {"role": Membership.Role.MEMBER},
        )

        self.assertEqual(remove.status_code, 403)
        self.assertEqual(demote.status_code, 403)
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, Membership.Role.ADMIN)


class OrganizationInvitationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@nebula.local",
            password="admin-password",
            full_name="Admin Nebula",
            email_verified=True,
        )
        self.invitee = user_model.objects.create_user(
            email="invitee@example.local",
            password="invitee-password",
            full_name="Invited User",
            email_verified=True,
        )
        self.other = user_model.objects.create_user(
            email="other@example.local",
            password="other-password",
            full_name="Other User",
            email_verified=True,
        )
        self.organization = Organization.objects.create(name="Nebula", slug="nebula")
        Membership.objects.create(
            user=self.admin,
            organization=self.organization,
            role=Membership.Role.ADMIN,
        )

    def create_invitation(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("organizations:invite-member"),
            {"email": self.invitee.email, "role": Membership.Role.MEMBER},
        )
        self.assertRedirects(response, reverse("organizations:overview"))
        return Invitation.objects.get()

    def test_admin_can_invite_and_local_email_contains_link(self):
        invitation = self.create_invitation()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(invitation.token, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.invitee.email])

    def test_matching_authenticated_user_can_accept_invitation(self):
        invitation = self.create_invitation()
        self.client.force_login(self.invitee)

        response = self.client.post(
            reverse("organizations:accept-invitation", args=[invitation.token])
        )

        self.assertRedirects(response, reverse("organizations:overview"))
        self.assertTrue(
            Membership.objects.filter(user=self.invitee, organization=self.organization).exists()
        )
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.accepted_at)

    def test_different_authenticated_user_cannot_accept_invitation(self):
        invitation = self.create_invitation()
        self.client.force_login(self.other)

        response = self.client.post(
            reverse("organizations:accept-invitation", args=[invitation.token])
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Membership.objects.filter(user=self.other, organization=self.organization).exists()
        )

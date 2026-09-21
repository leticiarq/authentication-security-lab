from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class PublicPagesTests(TestCase):
    def test_public_pages_render(self):
        for name in ("home", "about", "help", "terms"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "vaulta")

    def test_health_endpoint_is_small_and_public(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "vaulta-web"})

    def test_unknown_page_is_not_mistaken_for_product_content(self):
        response = self.client.get("/nao-existe/")

        self.assertEqual(response.status_code, 404)


class CustomUserTests(TestCase):
    def test_email_is_the_login_identifier(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            email="PESSOA@EXAMPLE.LOCAL",
            password="phase-one-test-password",
            full_name="Pessoa de Teste",
        )

        self.assertEqual(user.email, "pessoa@example.local")
        self.assertEqual(user.get_short_name(), "Pessoa")
        self.assertTrue(user.check_password("phase-one-test-password"))
        self.assertIsNone(user.username)

    def test_user_email_is_required(self):
        user_model = get_user_model()

        with self.assertRaisesMessage(ValueError, "O e-mail é obrigatório"):
            user_model.objects.create_user(email="", password="irrelevant")

    def test_organization_admin_is_not_a_global_user_role(self):
        user_model = get_user_model()

        self.assertEqual(
            {value for value, _label in user_model.Role.choices},
            {"regular", "system_admin"},
        )

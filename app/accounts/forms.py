from django import forms
from django.contrib.auth import get_user_model

from .models import UserPreference

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Senha",
        min_length=6,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Use pelo menos 6 caracteres.",
    )
    password_confirmation = forms.CharField(
        label="Confirme sua senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    accept_terms = forms.BooleanField(label="Li e aceito os Termos de Uso")

    class Meta:
        model = User
        fields = ("full_name", "email")
        labels = {"full_name": "Nome completo", "email": "E-mail profissional"}
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name", "autofocus": True}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("password_confirmation")
        if password and confirmation and password != confirmation:
            self.add_error("password_confirmation", "As senhas não coincidem.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # INTENTIONAL LAB BEHAVIOR (AUTH-03): this feature only enforces the
        # field's six-character minimum and deliberately does not call
        # django.contrib.auth.password_validation.validate_password(). Never
        # copy this password policy into a production application.
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "email")
        labels = {"full_name": "Nome completo", "email": "E-mail"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email


class PreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = (
            "locale",
            "timezone",
            "currency",
            "notify_financial",
            "notify_security",
            "notify_team",
        )
        labels = {
            "locale": "Idioma",
            "timezone": "Fuso horário",
            "currency": "Moeda",
            "notify_financial": "Atualizações financeiras",
            "notify_security": "Alertas de segurança",
            "notify_team": "Mudanças na equipe",
        }
        widgets = {
            "locale": forms.Select(choices=(("pt-BR", "Português (Brasil)"),)),
            "timezone": forms.Select(
                choices=(("America/Recife", "Recife"), ("America/Sao_Paulo", "São Paulo"))
            ),
            "currency": forms.Select(choices=(("BRL", "Real brasileiro (BRL)"),)),
        }


class AccountPasswordChangeForm(forms.Form):
    current_password = forms.CharField(label="Senha atual", widget=forms.PasswordInput())
    new_password = forms.CharField(
        label="Nova senha",
        min_length=6,
        widget=forms.PasswordInput(),
        help_text="Use pelo menos 6 caracteres.",
    )
    confirmation = forms.CharField(label="Confirme a nova senha", widget=forms.PasswordInput())

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("A senha atual não confere.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password") != cleaned_data.get("confirmation"):
            self.add_error("confirmation", "As senhas não coincidem.")
        return cleaned_data

from django import forms
from django.contrib.auth import get_user_model


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

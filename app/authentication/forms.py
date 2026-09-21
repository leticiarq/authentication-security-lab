from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    remember_me = forms.BooleanField(label="Manter conectado", required=False)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class PasswordRecoveryRequestForm(forms.Form):
    email = forms.EmailField(
        label="E-mail da conta",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class SetNewPasswordForm(forms.Form):
    # INTENTIONAL LAB BEHAVIOR (AUTH-03): recovery mirrors registration's
    # six-character-only policy and skips Django's password validators.
    password = forms.CharField(
        label="Nova senha",
        min_length=6,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Use pelo menos 6 caracteres.",
    )
    password_confirmation = forms.CharField(
        label="Confirme a nova senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("password_confirmation")
        if password and confirmation and password != confirmation:
            self.add_error("password_confirmation", "As senhas não coincidem.")
        return cleaned_data

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

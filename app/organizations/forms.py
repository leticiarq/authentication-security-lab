from django import forms

from .models import Membership


class InvitationForm(forms.Form):
    email = forms.EmailField(label="E-mail do novo membro")
    role = forms.ChoiceField(label="Papel", choices=Membership.Role.choices)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

from django import forms

from .models import Role


class OnboardingForm(forms.Form):
    organization = forms.CharField(
        label="Organization name", max_length=200,
        help_text="Your group or organization. You can add more companies later.",
    )
    company = forms.CharField(
        label="First company", max_length=200, required=False,
        help_text="Leave empty to use the organization name.",
    )


class InviteForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=Role.choices, initial=Role.MEMBER)

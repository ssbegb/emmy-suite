from django import forms

from emmy.tenancy.models import Company, Membership


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "legal_name", "registration_number", "email", "phone", "website", "address", "country"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class NewCompanyForm(forms.Form):
    name = forms.CharField(max_length=200, label="Company name")


class MembershipRoleForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["role"]

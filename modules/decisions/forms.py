from django import forms
from django.contrib.auth import get_user_model

from .models import Decision


class DecisionForm(forms.ModelForm):
    wide_fields = ["title", "context", "options", "decision", "rationale"]

    class Meta:
        model = Decision
        fields = ["title", "status", "owner", "context", "options", "decision", "rationale", "decided_on", "review_on"]
        widgets = {
            "decided_on": forms.DateInput(attrs={"type": "date"}),
            "review_on": forms.DateInput(attrs={"type": "date"}),
            **{f: forms.Textarea(attrs={"rows": 4}) for f in ["context", "options", "decision", "rationale"]},
        }

    def __init__(self, *args, company, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.company = company
        self.instance.tenant_id = company.tenant_id
        self.fields["owner"].queryset = get_user_model().objects.filter(memberships__company=company)

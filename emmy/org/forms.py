from django import forms
from django.contrib.auth import get_user_model

from .models import Department, Employee


class CompanyFormMixin:
    """Bind the form to a company and limit every choice to that company."""

    def __init__(self, *args, company, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.company = company
        self.instance.tenant_id = company.tenant_id


class DepartmentForm(CompanyFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "parent", "head"]

    def __init__(self, *args, company, **kwargs):
        super().__init__(*args, company=company, **kwargs)
        parents = Department.objects.filter(company=company)
        if self.instance.pk:
            parents = parents.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = parents
        self.fields["head"].queryset = Employee.objects.filter(company=company, is_active=True)

    def clean(self):
        data = super().clean()
        siblings = Department.objects.filter(
            company=self.instance.company, parent=data.get("parent"), name__iexact=data.get("name", "")
        ).exclude(pk=self.instance.pk)
        if data.get("name") and siblings.exists():
            self.add_error("name", "There is already a department with this name here.")
        return data


class EmployeeForm(CompanyFormMixin, forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["first_name", "last_name", "job_title", "email", "phone", "department", "manager", "user", "is_active"]

    def __init__(self, *args, company, **kwargs):
        super().__init__(*args, company=company, **kwargs)
        self.fields["department"].queryset = Department.objects.filter(company=company)
        managers = Employee.objects.filter(company=company, is_active=True)
        if self.instance.pk:
            managers = managers.exclude(pk=self.instance.pk)
        self.fields["manager"].queryset = managers
        self.fields["user"].queryset = get_user_model().objects.filter(memberships__company=company)
        self.fields["user"].label = "Login"

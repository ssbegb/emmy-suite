from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from emmy.tenancy.models import CompanyScoped


def _check_no_cycle(obj, field):
    """Walk up the tree from ``obj`` and fail if we come back to it."""
    seen = {obj.pk}
    node = getattr(obj, field)
    while node is not None:
        if node.pk in seen:
            raise ValidationError({field: "This would create a loop in the hierarchy."})
        seen.add(node.pk)
        node = getattr(node, field)


class Department(CompanyScoped):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
        help_text="Leave empty for a top-level department.",
    )
    head = models.ForeignKey(
        "Employee", null=True, blank=True, on_delete=models.SET_NULL, related_name="heads_of"
    )

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["company", "parent", "name"], name="uniq_department_name")]

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent_id and self.parent.company_id != self.company_id:
            raise ValidationError({"parent": "Choose a department in the same company."})
        if self.pk:
            _check_no_cycle(self, "parent")

    @property
    def path(self):
        names, node = [], self
        while node is not None:
            names.append(node.name)
            node = node.parent
        return " / ".join(reversed(names))


class Employee(CompanyScoped):
    """A person in the organization. Not every employee signs in, so the
    link to a user account is optional."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees"
    )
    manager = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reports"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="employee_records",
        help_text="Optional: link to the person's Emmy Suite login.",
    )
    is_active = models.BooleanField("active", default=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "user"], condition=models.Q(user__isnull=False), name="uniq_employee_user"
            )
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        if self.manager_id and self.manager_id == self.pk:
            raise ValidationError({"manager": "Someone can't be their own manager."})
        if self.pk and self.manager_id:
            _check_no_cycle(self, "manager")

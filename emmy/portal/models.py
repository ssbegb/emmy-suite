from django.db import models

from emmy.tenancy.models import CompanyScoped


class CompanyModule(CompanyScoped):
    """Whether a module is switched on for a company."""

    key = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)
    changed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "key"], name="uniq_company_module")]

    def __str__(self):
        return f"{self.key} @ {self.company_id}: {'on' if self.enabled else 'off'}"

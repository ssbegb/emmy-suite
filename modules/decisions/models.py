from django.conf import settings
from django.db import models

from emmy.tenancy.models import CompanyScoped


class Decision(CompanyScoped):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DECIDED = "decided", "Decided"
        REVIEWED = "reviewed", "Reviewed"

    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    context = models.TextField(blank=True, help_text="What is the situation, and why does it need a decision?")
    options = models.TextField("options considered", blank=True, help_text="The alternatives and their trade-offs.")
    decision = models.TextField("what we decided", blank=True)
    rationale = models.TextField("why", blank=True, help_text="Who is affected, and how does this fit our values?")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    decided_on = models.DateField(null=True, blank=True)
    review_on = models.DateField("review on", null=True, blank=True, help_text="When to check whether it worked.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

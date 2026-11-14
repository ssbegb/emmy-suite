import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .context import current_tenant_id


class Tenant(models.Model):
    """A customer organization. Tenants are completely sealed off from
    each other."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TenantScoped(models.Model):
    """Base for every table that belongs to a tenant."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, editable=False, related_name="+")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            self.tenant_id = self._infer_tenant_id()
        super().save(*args, **kwargs)

    def _infer_tenant_id(self):
        tenant_id = current_tenant_id()
        if not tenant_id:
            raise RuntimeError(f"No tenant in context when saving {type(self).__name__}")
        return tenant_id


class Company(TenantScoped):
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    registration_number = models.CharField("registration / VAT number", max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class CompanyScoped(TenantScoped):
    """Base for data that belongs to one company inside a tenant."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, editable=False, related_name="+")

    class Meta:
        abstract = True

    def _infer_tenant_id(self):
        if self.company_id:
            return self.company.tenant_id
        return super()._infer_tenant_id()


class Role(models.TextChoices):
    ADMIN = "admin", "Administrator"
    MANAGER = "manager", "Manager"
    MEMBER = "member", "Member"


ROLE_RANK = {Role.MEMBER: 1, Role.MANAGER: 2, Role.ADMIN: 3}


class Membership(CompanyScoped):
    """Gives a user access to one company with a role."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, editable=False, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "user"], name="uniq_membership")]
        ordering = ["user__email"]

    def __str__(self):
        return f"{self.user} @ {self.company} ({self.role})"

    def has_role(self, role):
        return ROLE_RANK[self.role] >= ROLE_RANK[role]

    @property
    def is_admin(self):
        return self.role == Role.ADMIN


def _token():
    return secrets.token_urlsafe(32)


def _expiry():
    return timezone.now() + timezone.timedelta(days=14)


class Invitation(CompanyScoped):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, editable=False, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    token = models.CharField(max_length=64, unique=True, default=_token, editable=False)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitation for {self.email} to {self.company}"

    @property
    def is_pending(self):
        return self.accepted_at is None and self.expires_at > timezone.now()

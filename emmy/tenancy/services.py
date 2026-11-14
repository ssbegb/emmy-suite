import uuid

from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .context import set_context
from .models import Company, Invitation, Membership, Role, Tenant


class InvitationError(Exception):
    pass


@transaction.atomic
def create_organization(user, organization_name, company_name=None):
    """Create a new tenant with its first company; ``user`` becomes admin."""
    tenant_id = uuid.uuid4()
    set_context(tenant_id, user.pk)
    tenant = Tenant.objects.create(id=tenant_id, name=organization_name)
    company = Company.objects.create(tenant=tenant, name=company_name or organization_name)
    return Membership.objects.create(company=company, tenant=tenant, user=user, role=Role.ADMIN)


def create_company(tenant, name, creator):
    company = Company.objects.create(tenant=tenant, name=name)
    Membership.objects.create(company=company, tenant=tenant, user=creator, role=Role.ADMIN)
    return company


def send_invitation(request, company, email, role):
    email = email.strip().lower()
    if Membership.objects.filter(company=company, user__email__iexact=email).exists():
        raise InvitationError(f"{email} already has access to {company}.")
    Invitation.objects.filter(company=company, email__iexact=email, accepted_at__isnull=True).delete()
    invitation = Invitation.objects.create(
        company=company, email=email, role=role, invited_by=request.user
    )
    link = request.build_absolute_uri(reverse("tenancy:accept_invite", args=[invitation.token]))
    context = {"invitation": invitation, "link": link, "inviter": request.user}
    send_mail(
        subject=f"You're invited to {company} on Emmy Suite",
        message=render_to_string("tenancy/email/invitation.txt", context),
        from_email=None,
        recipient_list=[email],
    )
    return invitation


def find_invitation(token, user=None):
    """Look up an invitation by its secret token (and nothing else)."""
    set_context(None, getattr(user, "pk", None), invite_token=token)
    invitation = Invitation.objects.filter(token=token).first()
    if invitation is None:
        return None
    # Now that we know the tenant, we may read the rest of its data.
    set_context(invitation.tenant_id, getattr(user, "pk", None), invite_token=token)
    return invitation


@transaction.atomic
def accept_invitation(invitation, user):
    if not invitation.is_pending:
        raise InvitationError("This invitation has expired or was already used.")
    if invitation.email.lower() != user.email.lower():
        raise InvitationError(
            f"This invitation was sent to {invitation.email}. Sign in with that address to accept it."
        )
    membership, created = Membership.objects.get_or_create(
        company=invitation.company,
        user=user,
        defaults={"tenant_id": invitation.tenant_id, "role": invitation.role},
    )
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["accepted_at"])
    return membership

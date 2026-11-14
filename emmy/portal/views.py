from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from emmy.accounts.forms import ProfileForm
from emmy.tenancy.decorators import company_required, role_required
from emmy.tenancy.forms import InviteForm
from emmy.tenancy.middleware import SESSION_KEY
from emmy.tenancy.models import Company, Invitation, Membership, Role
from emmy.tenancy.services import InvitationError, create_company, send_invitation

from .forms import CompanyForm, MembershipRoleForm, NewCompanyForm
from .models import CompanyModule
from .modules import available_modules, enabled_keys, get_module, optional_modules


@company_required
def home(request):
    return render(request, "portal/home.html", {"tiles": available_modules(request)})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile saved.")
        return redirect("portal:profile")
    return render(request, "portal/profile.html", {"form": form})


# --- Settings ---------------------------------------------------------------


@role_required(Role.ADMIN)
def settings_index(request):
    return redirect("portal:settings_company")


@role_required(Role.ADMIN)
def settings_company(request):
    form = CompanyForm(request.POST or None, instance=request.company)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Company details saved.")
        return redirect("portal:settings_company")
    return render(request, "portal/settings/company.html", {"form": form, "tab": "company"})


@role_required(Role.ADMIN)
def settings_companies(request):
    companies = Company.objects.filter(tenant=request.tenant)
    my_companies = {m.company_id for m in request.memberships}
    form = NewCompanyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        company = create_company(request.tenant, form.cleaned_data["name"], request.user)
        request.session[SESSION_KEY] = company.pk
        messages.success(request, f"{company} created. You're now working in it.")
        return redirect("portal:settings_company")
    return render(
        request,
        "portal/settings/companies.html",
        {"companies": companies, "my_companies": my_companies, "form": form, "tab": "companies"},
    )


@role_required(Role.ADMIN)
def settings_users(request):
    memberships = Membership.objects.filter(company=request.company).select_related("user")
    invitations = [
        i for i in Invitation.objects.filter(company=request.company, accepted_at__isnull=True) if i.is_pending
    ]
    form = InviteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            invitation = send_invitation(
                request, request.company, form.cleaned_data["email"], form.cleaned_data["role"]
            )
        except InvitationError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Invitation sent to {invitation.email}.")
            return redirect("portal:settings_users")
    return render(
        request,
        "portal/settings/users.html",
        {"memberships": memberships, "invitations": invitations, "form": form, "roles": Role.choices, "tab": "users"},
    )


def _other_admins(membership):
    return Membership.objects.filter(company=membership.company, role=Role.ADMIN).exclude(pk=membership.pk)


@role_required(Role.ADMIN)
@require_POST
def settings_user_role(request, pk):
    membership = get_object_or_404(Membership, pk=pk, company=request.company)
    was_admin = membership.role == Role.ADMIN  # read before the form updates the instance
    form = MembershipRoleForm(request.POST, instance=membership)
    if form.is_valid():
        if was_admin and form.cleaned_data["role"] != Role.ADMIN and not _other_admins(membership).exists():
            messages.error(request, "A company needs at least one administrator.")
        else:
            form.save()
            messages.success(request, f"{membership.user} is now {membership.get_role_display().lower()}.")
    return redirect("portal:settings_users")


@role_required(Role.ADMIN)
@require_POST
def settings_user_remove(request, pk):
    membership = get_object_or_404(Membership, pk=pk, company=request.company)
    if membership.role == Role.ADMIN and not _other_admins(membership).exists():
        messages.error(request, "A company needs at least one administrator.")
    else:
        membership.delete()
        messages.success(request, f"{membership.user} no longer has access to {request.company}.")
    return redirect("portal:settings_users")


@role_required(Role.ADMIN)
@require_POST
def settings_invite_cancel(request, pk):
    get_object_or_404(Invitation, pk=pk, company=request.company).delete()
    messages.success(request, "Invitation cancelled.")
    return redirect("portal:settings_users")


@role_required(Role.ADMIN)
def settings_modules(request):
    enabled = enabled_keys(request.company)
    modules = [(m, m.key in enabled) for m in optional_modules()]
    return render(request, "portal/settings/modules.html", {"modules": modules, "tab": "modules"})


@role_required(Role.ADMIN)
@require_POST
def settings_module_toggle(request, key):
    module = get_module(key)
    if module is None or module.core:
        messages.error(request, "Unknown module.")
        return redirect("portal:settings_modules")
    turn_on = request.POST.get("enabled") == "1"
    CompanyModule.objects.update_or_create(
        company=request.company, key=key, defaults={"enabled": turn_on, "tenant_id": request.company.tenant_id}
    )
    messages.success(request, f"{module.name} switched {'on' if turn_on else 'off'} for {request.company}.")
    return redirect("portal:settings_modules")

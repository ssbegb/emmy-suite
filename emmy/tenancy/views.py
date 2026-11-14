from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import OnboardingForm
from .middleware import SESSION_KEY
from .services import InvitationError, accept_invitation, create_organization, find_invitation


@login_required
def onboarding(request):
    if request.memberships:
        return redirect("portal:home")
    form = OnboardingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        membership = create_organization(
            request.user, form.cleaned_data["organization"], form.cleaned_data["company"]
        )
        request.session[SESSION_KEY] = membership.company_id
        messages.success(request, f"Welcome to Emmy Suite! {membership.company} is ready.")
        return redirect("portal:home")
    return render(request, "tenancy/onboarding.html", {"form": form})


@login_required
@require_POST
def switch_company(request):
    try:
        company_id = int(request.POST.get("company", ""))
    except ValueError:
        company_id = None
    if any(m.company_id == company_id for m in request.memberships):
        request.session[SESSION_KEY] = company_id
    return redirect(request.POST.get("next") or "portal:home")


def accept_invite(request, token):
    user = request.user if request.user.is_authenticated else None
    invitation = find_invitation(token, user)
    if invitation is None or not invitation.is_pending:
        return render(request, "tenancy/invite_invalid.html", status=404)
    if user is None:
        return render(request, "tenancy/invite_welcome.html", {"invitation": invitation})
    if request.method == "POST":
        try:
            membership = accept_invitation(invitation, user)
        except InvitationError as exc:
            messages.error(request, str(exc))
        else:
            request.session[SESSION_KEY] = membership.company_id
            messages.success(request, f"You now have access to {membership.company}.")
            return redirect("portal:home")
    return render(request, "tenancy/invite_accept.html", {"invitation": invitation})

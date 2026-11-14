from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def company_required(view):
    """Signed-in user who is working inside a company."""

    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.company is None:
            return redirect("tenancy:onboarding")
        return view(request, *args, **kwargs)

    return wrapper


def role_required(role):
    def decorator(view):
        @company_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.membership.has_role(role):
                raise PermissionDenied("You don't have permission to do that.")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator

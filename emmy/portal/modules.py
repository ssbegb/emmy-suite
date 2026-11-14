"""The module registry.

A module is a normal Django app whose AppConfig has an ``emmy_module``
attribute. Core modules are always available; the others are switched on
per company in Settings > Modules.
"""
from dataclasses import dataclass
from functools import wraps

from django.apps import apps
from django.contrib import messages
from django.shortcuts import redirect


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    name: str
    description: str
    url_name: str
    icon: str = "grid"
    color: str = "#4f46e5"
    core: bool = False
    admin_only: bool = False
    order: int = 50


def all_modules():
    specs = [cfg.emmy_module for cfg in apps.get_app_configs() if getattr(cfg, "emmy_module", None)]
    return sorted(specs, key=lambda m: (m.order, m.name))


def optional_modules():
    return [m for m in all_modules() if not m.core]


def get_module(key):
    return next((m for m in all_modules() if m.key == key), None)


def enabled_keys(company):
    from .models import CompanyModule

    return set(CompanyModule.objects.filter(company=company, enabled=True).values_list("key", flat=True))


def available_modules(request):
    """Modules the current user may open in the current company."""
    if request.company is None:
        return []
    keys = enabled_keys(request.company)
    result = []
    for module in all_modules():
        if module.admin_only and not request.membership.is_admin:
            continue
        if module.core or module.key in keys:
            result.append(module)
    return result


def module_required(key):
    """View decorator: the module must be switched on for the current company."""
    from emmy.tenancy.decorators import company_required

    def decorator(view):
        @company_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            module = get_module(key)
            if module and not module.core and key not in enabled_keys(request.company):
                messages.info(request, f"{module.name} isn't switched on for {request.company}.")
                return redirect("portal:home")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator

from django.apps import AppConfig

from .modules import ModuleSpec


class PortalConfig(AppConfig):
    name = "emmy.portal"
    label = "portal"
    verbose_name = "Portal"
    emmy_module = ModuleSpec(
        key="settings", name="Settings", description="Companies, users, roles and modules.",
        url_name="portal:settings", icon="settings", color="#64748b", core=True, admin_only=True, order=100,
    )

from django.apps import AppConfig

from emmy.portal.modules import ModuleSpec


class OrgConfig(AppConfig):
    name = "emmy.org"
    label = "org"
    verbose_name = "Organization"
    emmy_module = ModuleSpec(
        key="org", name="Organization", description="Departments, people and the org chart.",
        url_name="org:chart", icon="network", color="#0d9488", core=True, order=10,
    )

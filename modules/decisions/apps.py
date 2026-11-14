from django.apps import AppConfig

from emmy.portal.modules import ModuleSpec


class DecisionsConfig(AppConfig):
    name = "modules.decisions"
    label = "decisions"
    verbose_name = "Decisions"
    emmy_module = ModuleSpec(
        key="decisions", name="Decisions",
        description="Record important decisions: the context, the options weighed, what was decided and why.",
        url_name="decisions:index", icon="scale", color="#7c3aed", order=20,
    )

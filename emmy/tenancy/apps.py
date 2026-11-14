from django.apps import AppConfig


class TenancyConfig(AppConfig):
    name = "emmy.tenancy"
    label = "tenancy"
    verbose_name = "Tenancy"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .rls import grant_app_role

        post_migrate.connect(grant_app_role, dispatch_uid="emmy-grant-app-role")

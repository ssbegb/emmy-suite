from django.conf import settings
from django.db import connections
from django.db.backends.signals import connection_created
from django.test.runner import DiscoverRunner


def _use_app_role(sender, connection, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute(f'SET ROLE "{settings.DB_APP_USER}"')


class RLSTestRunner(DiscoverRunner):
    """Create the test database as the owner, then run every test as the
    limited app role so row-level security is enforced exactly as in
    production."""

    def setup_databases(self, **kwargs):
        config = super().setup_databases(**kwargs)
        connection_created.connect(_use_app_role, dispatch_uid="emmy-test-app-role")
        for conn in connections.all():
            conn.close()
        return config

    def teardown_databases(self, old_config, **kwargs):
        connection_created.disconnect(dispatch_uid="emmy-test-app-role")
        for conn in connections.all():
            conn.close()
        super().teardown_databases(old_config, **kwargs)

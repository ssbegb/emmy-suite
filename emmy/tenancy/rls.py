"""Row-level security helpers.

Every tenant-owned table gets a policy that only exposes rows whose
``tenant_id`` matches ``app.tenant_id`` for the current connection. The app
connects as a role without BYPASSRLS, so even a buggy query cannot read
another customer's data.
"""
from django.conf import settings
from django.db import connection, migrations

FUNCTIONS_SQL = """
CREATE OR REPLACE FUNCTION emmy_current_tenant() RETURNS uuid
    LANGUAGE sql STABLE AS
    $$ SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid $$;
CREATE OR REPLACE FUNCTION emmy_current_user() RETURNS bigint
    LANGUAGE sql STABLE AS
    $$ SELECT NULLIF(current_setting('app.user_id', true), '')::bigint $$;
CREATE OR REPLACE FUNCTION emmy_invite_token() RETURNS text
    LANGUAGE sql STABLE AS
    $$ SELECT NULLIF(current_setting('app.invite_token', true), '') $$;
"""


def enable_rls(table, using="tenant_id = emmy_current_tenant()", check=None):
    """Migration operation: turn on RLS for ``table`` with a single policy."""
    check = check or "tenant_id = emmy_current_tenant()"
    return migrations.RunSQL(
        sql=f"""
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
            ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS emmy_isolation ON {table};
            CREATE POLICY emmy_isolation ON {table}
                USING ({using}) WITH CHECK ({check});
        """,
        reverse_sql=f"""
            DROP POLICY IF EXISTS emmy_isolation ON {table};
            ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;
            ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
        """,
    )


def grant_app_role(sender=None, using="default", **kwargs):
    """After migrations, let the app role use every table (RLS still applies)."""
    role = settings.DB_APP_USER
    if not role or connection.settings_dict["USER"] == role:
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
        if not cursor.fetchone():
            return
        cursor.execute(
            f'GRANT USAGE ON SCHEMA public TO "{role}";'
            f' GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{role}";'
            f' GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{role}";'
            f' GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "{role}";'
        )

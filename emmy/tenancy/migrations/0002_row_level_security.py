from django.db import migrations

from emmy.tenancy.rls import FUNCTIONS_SQL, enable_rls

MY_TENANTS = "SELECT tenant_id FROM tenancy_membership WHERE user_id = emmy_current_user()"
MY_COMPANIES = "SELECT company_id FROM tenancy_membership WHERE user_id = emmy_current_user()"


class Migration(migrations.Migration):
    dependencies = [("tenancy", "0001_initial")]

    operations = [
        migrations.RunSQL(FUNCTIONS_SQL, reverse_sql=migrations.RunSQL.noop),
        # A user can always see the tenants and companies they belong to
        # (for the company switcher), but nothing else outside the current tenant.
        enable_rls(
            "tenancy_tenant",
            using=f"id = emmy_current_tenant() OR id IN ({MY_TENANTS})",
            check="id = emmy_current_tenant()",
        ),
        enable_rls(
            "tenancy_company",
            using=f"tenant_id = emmy_current_tenant() OR id IN ({MY_COMPANIES})",
        ),
        enable_rls(
            "tenancy_membership",
            using="tenant_id = emmy_current_tenant() OR user_id = emmy_current_user()",
        ),
        # An invitation can be read by whoever holds its secret token.
        enable_rls(
            "tenancy_invitation",
            using="tenant_id = emmy_current_tenant() OR token = emmy_invite_token()",
        ),
    ]

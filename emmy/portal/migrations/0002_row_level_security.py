from django.db import migrations

from emmy.tenancy.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("portal", "0001_initial"), ("tenancy", "0002_row_level_security")]

    operations = [
        enable_rls("portal_companymodule"),
    ]

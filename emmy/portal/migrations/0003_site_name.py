from django.db import migrations


def set_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(id=1, defaults={"domain": "localhost:8000", "name": "Emmy Suite"})


class Migration(migrations.Migration):
    dependencies = [("portal", "0002_row_level_security"), ("sites", "0002_alter_domain_unique")]
    operations = [migrations.RunPython(set_site, migrations.RunPython.noop)]

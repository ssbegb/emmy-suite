from django.test import TestCase

from emmy.tenancy.models import Membership, Role
from emmy.tenancy.testing import add_member, client_for, make_org, use


class PermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")
        cls.mia = add_member(cls.acme, "mia@acme.test", Role.MEMBER)

    def test_member_cannot_open_settings(self):
        for url in ["/settings/company/", "/settings/users/", "/settings/modules/", "/settings/companies/"]:
            self.assertEqual(client_for(self.mia).get(url).status_code, 403, url)

    def test_settings_tile_only_for_admins(self):
        self.assertContains(client_for(self.alice).get("/"), "Settings")
        self.assertNotContains(client_for(self.mia).get("/"), "/settings/")

    def test_last_admin_cannot_be_demoted_or_removed(self):
        use(self.acme)
        own = Membership.objects.get(user=self.alice)
        client = client_for(self.alice)
        client.post(f"/settings/users/{own.pk}/role/", {"role": Role.MEMBER})
        client.post(f"/settings/users/{own.pk}/remove/")
        use(self.acme)
        self.assertEqual(Membership.objects.get(user=self.alice).role, Role.ADMIN)

    def test_admin_changes_role_and_removes_user(self):
        use(self.acme)
        mia = Membership.objects.get(user=self.mia)
        client = client_for(self.alice)
        client.post(f"/settings/users/{mia.pk}/role/", {"role": Role.MANAGER})
        use(self.acme)
        mia.refresh_from_db()
        self.assertEqual(mia.role, Role.MANAGER)
        client.post(f"/settings/users/{mia.pk}/remove/")
        use(self.acme)
        self.assertFalse(Membership.objects.filter(user=self.mia).exists())

    def test_create_second_company(self):
        client = client_for(self.alice)
        client.post("/settings/companies/", {"name": "Acme Labs"})
        response = client.get("/")
        self.assertEqual(response.context["request"].company.name, "Acme Labs")
        self.assertEqual(len(response.context["request"].memberships), 2)


class ModuleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")
        cls.bob, cls.globex = make_org("bob@globex.test", "Globex")

    def test_module_is_off_until_switched_on(self):
        client = client_for(self.alice)
        self.assertRedirects(client.get("/decisions/"), "/")
        self.assertNotContains(client.get("/"), "/decisions/")
        client.post("/settings/modules/decisions/", {"enabled": "1"})
        self.assertEqual(client.get("/decisions/").status_code, 200)
        self.assertContains(client.get("/"), "/decisions/")

    def test_modules_are_per_company(self):
        client_for(self.alice).post("/settings/modules/decisions/", {"enabled": "1"})
        self.assertRedirects(client_for(self.bob).get("/decisions/"), "/")

    def test_switch_off(self):
        client = client_for(self.alice)
        client.post("/settings/modules/decisions/", {"enabled": "1"})
        client.post("/settings/modules/decisions/", {"enabled": "0"})
        self.assertRedirects(client.get("/decisions/"), "/")

    def test_core_modules_cannot_be_toggled(self):
        client_for(self.alice).post("/settings/modules/org/", {"enabled": "0"})
        self.assertEqual(client_for(self.alice).get("/org/").status_code, 200)

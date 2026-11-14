from django.test import TestCase

from emmy.tenancy.models import Role
from emmy.tenancy.testing import add_member, client_for, make_org, use

from .models import Department, Employee


class OrgTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")
        cls.top = Department.objects.create(company=cls.acme, name="Management")
        cls.sales = Department.objects.create(company=cls.acme, name="Sales", parent=cls.top)
        cls.boss = Employee.objects.create(company=cls.acme, first_name="Bea", department=cls.top)
        cls.rep = Employee.objects.create(company=cls.acme, first_name="Rui", department=cls.sales, manager=cls.boss)

    def test_chart_shows_tree(self):
        response = client_for(self.alice).get("/org/")
        tree = response.context["tree"]
        self.assertEqual(tree[0]["department"], self.top)
        self.assertEqual(tree[0]["children"][0]["department"], self.sales)
        self.assertContains(response, "Rui")

    def test_department_cannot_be_inside_its_own_child(self):
        response = client_for(self.alice).post(f"/org/departments/{self.top.pk}/", {"name": "Management", "parent": self.sales.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "loop")
        use(self.acme)
        self.top.refresh_from_db()
        self.assertIsNone(self.top.parent_id)

    def test_manager_loop_is_rejected(self):
        response = client_for(self.alice).post(
            f"/org/people/{self.boss.pk}/", {"first_name": "Bea", "manager": self.rep.pk, "is_active": "on"}
        )
        self.assertContains(response, "loop")

    def test_duplicate_sibling_department_name(self):
        response = client_for(self.alice).post("/org/departments/new/", {"name": "sales", "parent": self.top.pk})
        self.assertContains(response, "already a department")

    def test_department_with_children_cannot_be_deleted(self):
        client_for(self.alice).post(f"/org/departments/{self.top.pk}/delete/")
        use(self.acme)
        self.assertTrue(Department.objects.filter(pk=self.top.pk).exists())

    def test_members_can_view_but_not_edit(self):
        mia = add_member(self.acme, "mia@acme.test", Role.MEMBER)
        client = client_for(mia)
        self.assertEqual(client.get("/org/people/").status_code, 200)
        self.assertEqual(client.get("/org/people/new/").status_code, 403)
        self.assertEqual(client.post(f"/org/people/{self.rep.pk}/delete/").status_code, 403)

    def test_choices_limited_to_own_company(self):
        _, globex = make_org("bob@globex.test", "Globex")
        use(globex)
        other = Department.objects.create(company=globex, name="Other")
        response = client_for(self.alice).post("/org/people/new/", {"first_name": "X", "department": other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("department"))

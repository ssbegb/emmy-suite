from django.core import mail
from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from emmy.org.models import Employee

from .context import clear_context, set_context
from .models import Company, Invitation, Membership, Role, Tenant
from .testing import add_member, client_for, make_org, make_user, use


class RowLevelSecurityTests(TestCase):
    """The database itself keeps tenants apart, whatever the app code does."""

    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")
        Employee.objects.create(company=cls.acme, first_name="Acme person")
        cls.bob, cls.globex = make_org("bob@globex.test", "Globex")
        Employee.objects.create(company=cls.globex, first_name="Globex person")

    def test_runs_as_limited_role(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, rolbypassrls, rolsuper FROM pg_roles WHERE rolname = current_user")
            user, bypass, superuser = cursor.fetchone()
        self.assertFalse(bypass or superuser, f"tests must run as the limited role, not {user}")

    def test_only_current_tenant_is_visible(self):
        use(self.acme)
        self.assertEqual([e.first_name for e in Employee.objects.all()], ["Acme person"])
        self.assertEqual(list(Tenant.objects.values_list("name", flat=True)), ["Acme"])
        use(self.globex)
        self.assertEqual([e.first_name for e in Employee.objects.all()], ["Globex person"])

    def test_raw_sql_is_also_isolated(self):
        use(self.acme)
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM org_employee")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_no_context_sees_nothing(self):
        clear_context()
        self.assertEqual(Employee.objects.count(), 0)
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(Membership.objects.count(), 0)

    def test_cannot_write_into_another_tenant(self):
        use(self.acme)
        with self.assertRaises(Exception), transaction.atomic():
            Employee.objects.create(company_id=self.globex.pk, tenant_id=self.globex.tenant_id, first_name="Intruder")

    def test_cannot_move_rows_to_another_tenant(self):
        use(self.acme)
        with self.assertRaises(Exception), transaction.atomic():
            Employee.objects.filter(company=self.acme).update(tenant_id=self.globex.tenant_id)

    def test_user_sees_own_memberships_across_tenants(self):
        use(self.acme)
        Membership.objects.create(company=self.acme, tenant_id=self.acme.tenant_id, user=self.bob, role=Role.MEMBER)
        set_context(None, self.bob.pk)
        self.assertEqual(
            sorted(Membership.objects.filter(user=self.bob).values_list("company__name", flat=True)),
            ["Acme", "Globex"],
        )
        # ...but not other people's memberships, or the other tenant's data.
        self.assertFalse(Membership.objects.filter(user=self.alice).exists())
        self.assertEqual(Employee.objects.count(), 0)


class IsolationThroughTheAppTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")
        cls.acme_emp = Employee.objects.create(company=cls.acme, first_name="Ana")
        cls.bob, cls.globex = make_org("bob@globex.test", "Globex")

    def test_cannot_open_other_tenants_record(self):
        response = client_for(self.bob).get(f"/org/people/{self.acme_emp.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_cannot_switch_to_a_company_you_dont_belong_to(self):
        client = client_for(self.bob)
        client.post("/switch-company/", {"company": self.acme.pk})
        response = client.get("/org/people/")
        self.assertEqual(response.context["request"].company, self.globex)
        self.assertNotContains(response, "Ana")

    def test_user_without_company_goes_to_onboarding(self):
        user = make_user("new@example.test")
        response = client_for(user).get("/")
        self.assertRedirects(response, "/welcome/")


class SameTenantCompaniesTests(TestCase):
    """Inside one tenant, a user only reaches the companies they're a member of."""

    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")
        cls.subsidiary = Company.objects.create(tenant_id=cls.acme.tenant_id, name="Acme Labs")
        cls.lab_emp = Employee.objects.create(company=cls.subsidiary, first_name="Lab person")
        cls.carol = add_member(cls.acme, "carol@acme.test", Role.MANAGER)

    def test_member_of_one_company_cannot_open_sister_company_data(self):
        response = client_for(self.carol).get(f"/org/people/{self.lab_emp.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_switching_between_own_companies(self):
        use(self.acme)
        Membership.objects.create(company=self.subsidiary, tenant_id=self.acme.tenant_id, user=self.alice, role=Role.ADMIN)
        client = client_for(self.alice)
        client.post("/switch-company/", {"company": self.subsidiary.pk})
        self.assertContains(client.get("/org/people/"), "Lab person")


class InvitationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")

    def invite(self, email="dan@example.test", role=Role.MANAGER):
        client_for(self.alice).post("/settings/users/", {"email": email, "role": role})
        use(self.acme)
        return Invitation.objects.get(email=email)

    def test_invite_sends_email_with_link(self):
        invitation = self.invite()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"/invite/{invitation.token}/", mail.outbox[0].body)

    def test_accepting_creates_membership(self):
        invitation = self.invite()
        dan = make_user("dan@example.test")
        client = client_for(dan)
        self.assertContains(client.get(f"/invite/{invitation.token}/"), "Join Acme")
        response = client.post(f"/invite/{invitation.token}/")
        self.assertRedirects(response, "/")
        use(self.acme)
        membership = Membership.objects.get(user=dan)
        self.assertEqual((membership.company, membership.role), (self.acme, Role.MANAGER))
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.accepted_at)
        # The link can't be used twice.
        self.assertEqual(client.get(f"/invite/{invitation.token}/").status_code, 404)

    def test_wrong_email_cannot_accept(self):
        invitation = self.invite()
        eve = make_user("eve@example.test")
        client_for(eve).post(f"/invite/{invitation.token}/")
        use(self.acme)
        self.assertFalse(Membership.objects.filter(user=eve).exists())

    def test_anonymous_visitor_is_asked_to_sign_up(self):
        invitation = self.invite()
        response = self.client.get(f"/invite/{invitation.token}/", HTTP_HOST="localhost")
        self.assertContains(response, "Create account")

    def test_unknown_token(self):
        response = self.client.get("/invite/not-a-real-token/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 404)

    def test_cannot_invite_existing_member(self):
        client_for(self.alice).post("/settings/users/", {"email": "alice@acme.test", "role": Role.MEMBER})
        use(self.acme)
        self.assertFalse(Invitation.objects.exists())


class OnboardingTests(TestCase):
    def test_signup_then_create_organization(self):
        client = self.client
        client.defaults["HTTP_HOST"] = "localhost"
        client.post("/accounts/signup/", {"email": "new@example.test", "password1": "A-long-passw0rd", "password2": "A-long-passw0rd"})
        response = client.post("/welcome/", {"organization": "New Org", "company": "New Co"})
        self.assertRedirects(response, "/")
        self.assertContains(client.get("/"), "New Co")

from django.test import TestCase

from emmy.tenancy.testing import client_for, make_org, use

from .models import Decision


class DecisionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice, cls.acme = make_org("alice@acme.test", "Acme")

    def test_record_a_decision(self):
        client = client_for(self.alice)
        client.post("/settings/modules/decisions/", {"enabled": "1"})
        response = client.post("/decisions/new/", {"title": "Adopt a four-day week", "status": "open"})
        self.assertRedirects(response, "/decisions/")
        use(self.acme)
        decision = Decision.objects.get()
        self.assertEqual((decision.company, decision.tenant_id), (self.acme, self.acme.tenant_id))
        self.assertContains(client.get("/decisions/"), "Adopt a four-day week")

"""Helpers for tests."""
from django.contrib.auth import get_user_model
from django.test import Client

from .context import set_context
from .models import Membership, Role
from .services import create_organization

PASSWORD = "Correct-horse-battery-9"


def make_user(email):
    return get_user_model().objects.create_user(email=email, password=PASSWORD)


def make_org(email, name):
    """A tenant with one company, administered by a new user."""
    user = make_user(email)
    membership = create_organization(user, name)
    return user, membership.company


def add_member(company, email, role=Role.MEMBER):
    user = make_user(email)
    set_context(company.tenant_id, user.pk)
    Membership.objects.create(company=company, tenant_id=company.tenant_id, user=user, role=role)
    return user


def client_for(user):
    client = Client(HTTP_HOST="localhost")
    client.force_login(user)
    return client


def use(company, user=None):
    """Point the database at ``company``'s tenant (tests run under RLS)."""
    set_context(company.tenant_id, getattr(user, "pk", None))

"""The current tenant / user for this request, mirrored into PostgreSQL so
row-level security policies can enforce isolation in the database itself."""
from contextlib import contextmanager
from contextvars import ContextVar

from django.db import connection

_tenant_id: ContextVar = ContextVar("emmy_tenant_id", default=None)
_user_id: ContextVar = ContextVar("emmy_user_id", default=None)


def current_tenant_id():
    return _tenant_id.get()


def set_context(tenant_id=None, user_id=None, invite_token=None):
    """Set the tenant and user that the database will allow access to."""
    _tenant_id.set(tenant_id)
    _user_id.set(user_id)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, false),"
            " set_config('app.user_id', %s, false),"
            " set_config('app.invite_token', %s, false)",
            [str(tenant_id or ""), str(user_id or ""), invite_token or ""],
        )


def clear_context():
    set_context(None, None, None)


@contextmanager
def tenant_context(tenant_id, user_id=None, invite_token=None):
    previous = (_tenant_id.get(), _user_id.get())
    set_context(tenant_id, user_id if user_id is not None else previous[1], invite_token)
    try:
        yield
    finally:
        set_context(*previous)

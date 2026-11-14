from .context import clear_context, set_context
from .models import Membership

SESSION_KEY = "emmy_company_id"


class TenantMiddleware:
    """Work out which company the user is working in and tell the database.

    Sets ``request.membership``, ``request.company`` and ``request.tenant``
    (all ``None`` when the user has no company yet).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.membership = request.company = request.tenant = None
        request.memberships = []
        try:
            if request.user.is_authenticated:
                self._activate(request)
            return self.get_response(request)
        finally:
            clear_context()

    def _activate(self, request):
        user = request.user
        set_context(None, user.pk)
        memberships = list(
            Membership.objects.filter(user=user).select_related("company").order_by("company__name")
        )
        request.memberships = memberships
        if not memberships:
            return
        wanted = request.session.get(SESSION_KEY)
        membership = next((m for m in memberships if m.company_id == wanted), memberships[0])
        request.session[SESSION_KEY] = membership.company_id
        set_context(membership.tenant_id, user.pk)
        request.membership = membership
        request.company = membership.company
        request.tenant = membership.tenant

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from emmy.portal.modules import module_required

from .forms import DecisionForm
from .models import Decision


@module_required("decisions")
def index(request):
    decisions = Decision.objects.filter(company=request.company).select_related("owner")
    status = request.GET.get("status")
    if status in Decision.Status.values:
        decisions = decisions.filter(status=status)
    return render(
        request, "decisions/index.html",
        {"decisions": decisions, "status": status, "statuses": Decision.Status.choices},
    )


@module_required("decisions")
def edit(request, pk=None):
    instance = get_object_or_404(Decision, pk=pk, company=request.company) if pk else None
    initial = {} if instance else {"owner": request.user}
    form = DecisionForm(request.POST or None, instance=instance, initial=initial, company=request.company)
    if request.method == "POST" and form.is_valid():
        decision = form.save()
        messages.success(request, f"“{decision}” saved.")
        return redirect("decisions:index")
    return render(request, "decisions/form.html", {"form": form, "object": instance})

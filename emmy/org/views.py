from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from emmy.tenancy.decorators import company_required, role_required
from emmy.tenancy.models import Role

from .forms import DepartmentForm, EmployeeForm
from .models import Department, Employee


def _tree(company):
    departments = list(Department.objects.filter(company=company).select_related("head"))
    employees = list(Employee.objects.filter(company=company, is_active=True).select_related("manager"))
    children, staff = {}, {}
    for d in departments:
        children.setdefault(d.parent_id, []).append(d)
    for e in employees:
        staff.setdefault(e.department_id, []).append(e)

    def build(parent_id):
        return [
            {"department": d, "employees": staff.get(d.pk, []), "children": build(d.pk)}
            for d in children.get(parent_id, [])
        ]

    return build(None), staff.get(None, [])


@company_required
def chart(request):
    tree, unassigned = _tree(request.company)
    return render(request, "org/chart.html", {"tree": tree, "unassigned": unassigned, "tab": "chart"})


@company_required
def employee_list(request):
    employees = Employee.objects.filter(company=request.company).select_related("department", "manager")
    query = request.GET.get("q", "").strip()
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(job_title__icontains=query)
        )
    return render(request, "org/employee_list.html", {"employees": employees, "q": query, "tab": "people"})


@company_required
def department_list(request):
    departments = Department.objects.filter(company=request.company).select_related("parent", "head")
    return render(request, "org/department_list.html", {"departments": departments, "tab": "departments"})


def _edit(request, form_class, instance, template, success_url, label):
    form = form_class(request.POST or None, instance=instance, company=request.company)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"{label} “{obj}” saved.")
        return redirect(success_url)
    return render(request, template, {"form": form, "object": instance})


@role_required(Role.MANAGER)
def employee_edit(request, pk=None):
    instance = get_object_or_404(Employee, pk=pk, company=request.company) if pk else None
    return _edit(request, EmployeeForm, instance, "org/employee_form.html", "org:employees", "Employee")


@role_required(Role.MANAGER)
def department_edit(request, pk=None):
    instance = get_object_or_404(Department, pk=pk, company=request.company) if pk else None
    return _edit(request, DepartmentForm, instance, "org/department_form.html", "org:departments", "Department")


@role_required(Role.MANAGER)
@require_POST
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk, company=request.company)
    employee.delete()
    messages.success(request, f"{employee} removed.")
    return redirect("org:employees")


@role_required(Role.MANAGER)
@require_POST
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk, company=request.company)
    try:
        department.delete()
    except ProtectedError:
        messages.error(request, f"Move or delete the departments inside {department} first.")
    else:
        messages.success(request, f"{department} deleted.")
    return redirect("org:departments")

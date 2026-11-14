from django.urls import path

from . import views

app_name = "org"
urlpatterns = [
    path("", views.chart, name="chart"),
    path("people/", views.employee_list, name="employees"),
    path("people/new/", views.employee_edit, name="employee_new"),
    path("people/<int:pk>/", views.employee_edit, name="employee_edit"),
    path("people/<int:pk>/delete/", views.employee_delete, name="employee_delete"),
    path("departments/", views.department_list, name="departments"),
    path("departments/new/", views.department_edit, name="department_new"),
    path("departments/<int:pk>/", views.department_edit, name="department_edit"),
    path("departments/<int:pk>/delete/", views.department_delete, name="department_delete"),
]

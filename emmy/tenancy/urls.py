from django.urls import path

from . import views

app_name = "tenancy"
urlpatterns = [
    path("welcome/", views.onboarding, name="onboarding"),
    path("switch-company/", views.switch_company, name="switch_company"),
    path("invite/<str:token>/", views.accept_invite, name="accept_invite"),
]

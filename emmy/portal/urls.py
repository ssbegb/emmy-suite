from django.urls import path

from . import views

app_name = "portal"
urlpatterns = [
    path("", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings_index, name="settings"),
    path("settings/company/", views.settings_company, name="settings_company"),
    path("settings/companies/", views.settings_companies, name="settings_companies"),
    path("settings/users/", views.settings_users, name="settings_users"),
    path("settings/users/<int:pk>/role/", views.settings_user_role, name="settings_user_role"),
    path("settings/users/<int:pk>/remove/", views.settings_user_remove, name="settings_user_remove"),
    path("settings/invitations/<int:pk>/cancel/", views.settings_invite_cancel, name="settings_invite_cancel"),
    path("settings/modules/", views.settings_modules, name="settings_modules"),
    path("settings/modules/<str:key>/", views.settings_module_toggle, name="settings_module_toggle"),
]

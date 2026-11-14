from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("", include("emmy.tenancy.urls")),
    path("", include("emmy.portal.urls")),
    path("org/", include("emmy.org.urls")),
    path("decisions/", include("modules.decisions.urls")),
]

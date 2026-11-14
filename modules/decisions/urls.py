from django.urls import path

from . import views

app_name = "decisions"
urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.edit, name="new"),
    path("<int:pk>/", views.edit, name="edit"),
]

from django.urls import path

from . import views

app_name = "inteligencia"

urlpatterns = [
    path("inteligencia/", views.panel, name="panel"),
    path("inteligencia/version/<int:pk>/activar/", views.activar, name="activar"),
]

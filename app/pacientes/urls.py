from django.urls import path

from . import views

app_name = "pacientes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.crear, name="crear"),
    path("<int:pk>/", views.ficha, name="ficha"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/estado/", views.cambiar_estado, name="estado"),
    path(
        "antecedente/<int:pk>/quitar/",
        views.quitar_antecedente,
        name="quitar_antecedente",
    ),
]

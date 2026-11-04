from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.lista, name="inicio"),
    path("<str:entidad>/", views.lista, name="lista"),
    path("<str:entidad>/nuevo/", views.crear, name="crear"),
    path("<str:entidad>/<int:pk>/editar/", views.editar, name="editar"),
    path("<str:entidad>/<int:pk>/estado/", views.cambiar_estado, name="estado"),
]

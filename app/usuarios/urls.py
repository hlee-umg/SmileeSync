from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.crear, name='crear'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/estado/', views.cambiar_estado, name='cambiar_estado'),
    path('historial/', views.historial, name='historial'),
]

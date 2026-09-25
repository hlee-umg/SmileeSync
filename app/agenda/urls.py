from django.urls import path

from . import views

app_name = 'agenda'

urlpatterns = [
    path('', views.principal, name='principal'),
    path('citas/', views.lista, name='lista'),
    path('citas/nueva/', views.crear, name='crear'),
    path('citas/estimar/', views.estimar, name='estimar'),
    path('citas/<int:pk>/', views.detalle, name='detalle'),
    path('citas/<int:pk>/editar/', views.editar, name='editar'),
    path('citas/<int:pk>/cancelar/', views.cancelar, name='cancelar'),
    path('citas/<int:pk>/tiempos/', views.registrar_tiempos, name='tiempos'),
    path('horarios/<int:odontologo_id>/', views.horarios, name='horarios'),
    path('horarios/franja/<int:pk>/quitar/', views.quitar_horario, name='quitar_horario'),
]

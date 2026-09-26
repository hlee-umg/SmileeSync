from django.urls import path

from . import views

app_name = 'clinico'

urlpatterns = [
    path('expedientes/', views.lista, name='lista'),
    path('expedientes/<int:paciente_id>/', views.expediente, name='expediente'),
    path('expedientes/<int:paciente_id>/odontograma/', views.odontograma,
         name='odontograma'),
    path('expedientes/<int:paciente_id>/notas/', views.notas, name='notas'),
    path('expedientes/<int:paciente_id>/notas/nueva/', views.nota_nueva,
         name='nota_nueva'),
    path('expedientes/<int:paciente_id>/planes/nuevo/', views.plan_nuevo,
         name='plan_nuevo'),
    path('hallazgo/<int:pk>/quitar/', views.quitar_hallazgo, name='quitar_hallazgo'),

    path('planes/', views.planes, name='planes'),
    path('planes/<int:pk>/', views.plan_detalle, name='plan_detalle'),
    path('planes/<int:pk>/estado/', views.plan_estado, name='plan_estado'),
    path('planes/renglon/<int:pk>/quitar/', views.plan_quitar_detalle,
         name='quitar_renglon'),
    path('planes/renglon/<int:pk>/agendar/', views.agendar_renglon,
         name='agendar_renglon'),

    path('cobros/', views.cobros, name='cobros'),
    path('cobros/pago/<int:pk>/anular/', views.anular_pago, name='anular_pago'),
]

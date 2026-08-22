from django.contrib import admin
from .models import ModeloVersion, DatoEntrenamiento, Prediccion


@admin.register(ModeloVersion)
class ModeloVersionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'algoritmo', 'mae', 'rmse', 'r2', 'activo', 'estado')
    list_filter = ('algoritmo', 'activo', 'estado')


@admin.register(DatoEntrenamiento)
class DatoEntrenamientoAdmin(admin.ModelAdmin):
    list_display = ('tipo_procedimiento', 'odontologo', 'dia_semana', 'hora_inicio', 'num_piezas', 'duracion_real_min')
    list_filter = ('dia_semana',)


@admin.register(Prediccion)
class PrediccionAdmin(admin.ModelAdmin):
    list_display = ('cita', 'modelo', 'duracion_estimada_min', 'bloque_min_recomendado', 'bloque_max_recomendado', 'fecha')

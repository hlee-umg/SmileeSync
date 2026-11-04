from django.contrib import admin
from .models import Especialidad, Procedimiento, Odontologo


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre",)


@admin.register(Procedimiento)
class ProcedimientoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "especialidad",
        "nivel_complejidad",
        "duracion_promedio_min",
        "estado",
    )
    list_filter = ("especialidad", "nivel_complejidad", "estado")
    search_fields = ("codigo", "nombre")


@admin.register(Odontologo)
class OdontologoAdmin(admin.ModelAdmin):
    list_display = ("nombres", "apellidos", "especialidad", "colegiado", "estado")
    list_filter = ("especialidad", "estado")
    search_fields = ("nombres", "apellidos", "colegiado")

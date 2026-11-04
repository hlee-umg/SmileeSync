from django.contrib import admin
from .models import HorarioDisponibilidad, Cita, HistorialCita


@admin.register(HorarioDisponibilidad)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ("odontologo", "dia_semana", "hora_inicio", "hora_fin", "estado")
    list_filter = ("dia_semana", "estado")


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fecha",
        "paciente",
        "odontologo",
        "procedimiento",
        "estado_cita",
        "duracion_asignada_min",
        "duracion_real_min",
        "estado",
    )
    list_filter = ("estado_cita", "fecha", "odontologo", "estado")
    search_fields = ("paciente__nombres", "paciente__apellidos")
    date_hierarchy = "fecha"


@admin.register(HistorialCita)
class HistorialCitaAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "cita_ref",
        "paciente",
        "odontologo",
        "accion",
        "realizado_por",
    )
    list_filter = ("accion",)
    readonly_fields = [f.name for f in HistorialCita._meta.fields]

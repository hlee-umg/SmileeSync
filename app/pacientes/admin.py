from django.contrib import admin
from .models import Paciente, AntecedenteMedico, HistorialPaciente


class AntecedenteInline(admin.TabularInline):
    model = AntecedenteMedico
    extra = 0


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombres', 'apellidos', 'telefono', 'estado')
    list_filter = ('estado', 'sexo')
    search_fields = ('codigo', 'nombres', 'apellidos')
    inlines = [AntecedenteInline]


@admin.register(AntecedenteMedico)
class AntecedenteMedicoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'tipo', 'estado')
    list_filter = ('estado',)


@admin.register(HistorialPaciente)
class HistorialPacienteAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'codigo', 'nombre_completo', 'accion', 'realizado_por')
    list_filter = ('accion',)
    readonly_fields = [f.name for f in HistorialPaciente._meta.fields]

from django.contrib import admin

from .models import (DetallePlan, Hallazgo, HistorialPlan, NotaClinica, Pago,
                     PlanTratamiento)


class DetallePlanInline(admin.TabularInline):
    model = DetallePlan
    extra = 0


@admin.register(PlanTratamiento)
class PlanTratamientoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'paciente', 'odontologo', 'estado_plan', 'fecha')
    list_filter = ('estado_plan', 'estado')
    search_fields = ('codigo', 'paciente__nombres', 'paciente__apellidos')
    inlines = [DetallePlanInline]


@admin.register(Hallazgo)
class HallazgoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'pieza', 'cara', 'tipo', 'fecha')
    list_filter = ('tipo', 'estado')


@admin.register(NotaClinica)
class NotaClinicaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'odontologo', 'fecha', 'num_piezas', 'complicacion')
    list_filter = ('complicacion', 'anestesia', 'estado')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('plan', 'fecha', 'monto', 'metodo', 'estado')
    list_filter = ('metodo', 'estado')


admin.site.register(HistorialPlan)

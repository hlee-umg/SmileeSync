from django.contrib import admin
from .models import IndicadorDesempeno


@admin.register(IndicadorDesempeno)
class IndicadorDesempenoAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "citas_atendidas",
        "utilizacion_pct",
        "tiempo_espera_prom_min",
        "mae_actual",
        "rmse_actual",
        "r2_actual",
    )
    date_hierarchy = "fecha"

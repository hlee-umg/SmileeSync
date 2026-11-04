from django.db import models


class IndicadorDesempeno(models.Model):
    """Indicadores (KPIs) de la agenda y del modelo, calculados por fecha."""

    fecha = models.DateField("fecha")
    citas_atendidas = models.PositiveIntegerField("citas atendidas", default=0)
    utilizacion_pct = models.FloatField(
        "utilización de agenda (%)", null=True, blank=True
    )
    tiempo_espera_prom_min = models.FloatField(
        "tiempo de espera promedio (min)", null=True, blank=True
    )
    mae_actual = models.FloatField("MAE del modelo", null=True, blank=True)
    rmse_actual = models.FloatField("RMSE del modelo", null=True, blank=True)
    r2_actual = models.FloatField("R² del modelo", null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "indicador_desempeno"
        verbose_name = "Indicador de desempeño"
        verbose_name_plural = "Indicadores de desempeño"
        ordering = ["-fecha"]

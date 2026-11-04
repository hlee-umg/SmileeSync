from django.db import models


class ModeloVersion(models.Model):
    """Versión de un modelo predictivo entrenado y sus métricas."""

    ALGORITMOS = [("LINEAL", "Regresión lineal múltiple"), ("RF", "Random Forest")]
    nombre = models.CharField("nombre", max_length=80)
    algoritmo = models.CharField("algoritmo", max_length=10, choices=ALGORITMOS)
    mae = models.FloatField("MAE", null=True, blank=True)
    rmse = models.FloatField("RMSE", null=True, blank=True)
    r2 = models.FloatField("R²", null=True, blank=True)
    # Error de estimar con la duración de referencia del catálogo sobre el
    # MISMO subconjunto de prueba. Es la cifra contra la que se contrasta el
    # modelo para resolver la hipótesis del proyecto.
    mae_catalogo = models.FloatField("MAE del catálogo", null=True, blank=True)
    fecha_entrenamiento = models.DateTimeField(
        "fecha de entrenamiento", null=True, blank=True
    )
    ruta_archivo = models.CharField(
        "ruta del modelo (.joblib)", max_length=255, blank=True
    )
    activo = models.BooleanField("en producción", default=False)
    estado = models.BooleanField("activo", default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "modelo_version"
        verbose_name = "Versión de modelo"
        verbose_name_plural = "Versiones de modelo"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.nombre} ({self.get_algoritmo_display()})"


class DatoEntrenamiento(models.Model):
    """Conjunto de entrenamiento del modelo, materializado.

    Cada fila es una atención concluida con las siete variables con que se
    entrena y la duración real que se busca estimar. La tabla se mantiene al
    día desde dos puntos: al cerrar una cita y, antes de cada entrenamiento,
    con `entrenamiento.sincronizar()`, que da de alta las atenciones que
    falten, corrige las que cambiaron y da de baja las que dejaron de ser
    válidas (una cita cancelada después de haberse atendido, por ejemplo).

    Materializarla, en lugar de reconstruir el conjunto en cada entrenamiento,
    deja constancia de con qué datos se entrenó y conserva el valor que tenían
    la tarifa y la duración de referencia en ese momento.
    """

    cita = models.OneToOneField(
        "agenda.Cita",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dato_entrenamiento",
        verbose_name="cita origen",
    )
    tipo_procedimiento = models.CharField("tipo de procedimiento", max_length=120)
    odontologo = models.CharField("odontólogo", max_length=200)
    dia_semana = models.CharField("día de la semana", max_length=3)
    hora_inicio = models.PositiveIntegerField("hora de inicio (0-23)")
    num_piezas = models.PositiveIntegerField("número de piezas", default=1)
    anestesia = models.BooleanField("se aplicó anestesia", default=False)
    complicacion = models.BooleanField("hubo complicación", default=False)
    # Duración declarada en el catálogo cuando se atendió. Es la estimación
    # que el sistema habría usado sin modelo, y la línea base de la hipótesis.
    duracion_catalogo_min = models.PositiveIntegerField(
        "duración de referencia del catálogo (min)", default=0
    )
    duracion_real_min = models.PositiveIntegerField("duración real (min)")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dato_entrenamiento"
        verbose_name = "Dato de entrenamiento"
        verbose_name_plural = "Datos de entrenamiento"
        ordering = ["-creado"]


class Prediccion(models.Model):
    """Predicción de duración y recomendación de bloque para una cita."""

    cita = models.ForeignKey(
        "agenda.Cita",
        on_delete=models.CASCADE,
        related_name="predicciones",
        verbose_name="cita",
    )
    modelo = models.ForeignKey(
        ModeloVersion,
        on_delete=models.PROTECT,
        related_name="predicciones",
        verbose_name="modelo",
    )
    duracion_estimada_min = models.PositiveIntegerField("duración estimada (min)")
    bloque_min_recomendado = models.PositiveIntegerField("bloque mínimo (min)")
    bloque_max_recomendado = models.PositiveIntegerField("bloque máximo (min)")
    fecha = models.DateTimeField("fecha de la predicción", auto_now_add=True)

    class Meta:
        db_table = "prediccion"
        verbose_name = "Predicción"
        verbose_name_plural = "Predicciones"
        ordering = ["-fecha"]

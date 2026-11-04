from django.db import models


class Paciente(models.Model):
    """Paciente atendido en la clínica."""

    SEXO = [("M", "Masculino"), ("F", "Femenino")]
    codigo = models.CharField("código", max_length=20, unique=True)
    nombres = models.CharField("nombres", max_length=80)
    apellidos = models.CharField("apellidos", max_length=80)
    fecha_nacimiento = models.DateField("fecha de nacimiento", null=True, blank=True)
    sexo = models.CharField("sexo", max_length=1, choices=SEXO, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo", blank=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    estado = models.BooleanField("activo", default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "paciente"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.codigo} - {self.nombres} {self.apellidos}"


class AntecedenteMedico(models.Model):
    """Antecedente clínico o médico relevante de un paciente."""

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="antecedentes",
        verbose_name="paciente",
    )
    tipo = models.CharField("tipo", max_length=60)
    descripcion = models.TextField("descripción")
    estado = models.BooleanField("activo", default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "antecedente_medico"
        verbose_name = "Antecedente médico"
        verbose_name_plural = "Antecedentes médicos"

    def __str__(self):
        return f"{self.tipo} ({self.paciente})"


class HistorialPaciente(models.Model):
    """Tabla de histórico/auditoría del módulo de pacientes."""

    ACCIONES = [
        ("CREACION", "Creación"),
        ("ACTUALIZACION", "Actualización"),
        ("DESACTIVACION", "Desactivación"),
        ("ACTIVACION", "Activación"),
    ]
    paciente_ref = models.IntegerField("id de paciente")
    codigo = models.CharField(max_length=20)
    nombre_completo = models.CharField(max_length=200)
    estado_anterior = models.BooleanField()
    accion = models.CharField(max_length=20, choices=ACCIONES)
    realizado_por = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_paciente"
        verbose_name = "Historial de paciente"
        verbose_name_plural = "Historial de pacientes"
        ordering = ["-fecha"]

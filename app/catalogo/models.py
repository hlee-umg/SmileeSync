from django.db import models
from django.conf import settings


class Especialidad(models.Model):
    """Especialidad odontológica (p. ej. Endodoncia, Ortodoncia)."""
    nombre = models.CharField('nombre', max_length=80, unique=True)
    descripcion = models.CharField('descripción', max_length=200, blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'especialidad'
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Procedimiento(models.Model):
    """Catálogo de procedimientos odontológicos."""
    COMPLEJIDAD = [('BAJA', 'Baja'), ('MEDIA', 'Media'), ('ALTA', 'Alta')]
    codigo = models.CharField('código', max_length=20, unique=True)
    nombre = models.CharField('nombre', max_length=120)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT,
                                     related_name='procedimientos', verbose_name='especialidad')
    nivel_complejidad = models.CharField('nivel de complejidad', max_length=5,
                                         choices=COMPLEJIDAD, default='MEDIA')
    duracion_promedio_min = models.PositiveIntegerField('duración promedio (min)', default=30)
    descripcion = models.TextField('descripción', blank=True)
    estado = models.BooleanField('activo', default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procedimiento'
        verbose_name = 'Procedimiento'
        verbose_name_plural = 'Procedimientos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Odontologo(models.Model):
    """Profesional odontólogo de la clínica."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='odontologo',
                                verbose_name='usuario del sistema')
    nombres = models.CharField('nombres', max_length=80)
    apellidos = models.CharField('apellidos', max_length=80)
    colegiado = models.CharField('número de colegiado', max_length=30, blank=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT,
                                     related_name='odontologos', verbose_name='especialidad')
    telefono = models.CharField('teléfono', max_length=20, blank=True)
    estado = models.BooleanField('activo', default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'odontologo'
        verbose_name = 'Odontólogo'
        verbose_name_plural = 'Odontólogos'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'


class UnidadDental(models.Model):
    """Sillón o unidad dental de la clínica.

    Es el recurso físico que limita la operación: la clínica dispone de menos
    unidades que odontólogos, de modo que dos profesionales libres a la misma
    hora no implican dos citas simultáneas posibles. Las unidades son
    intercambiables, por lo que el sistema asigna la primera libre al programar.
    """
    codigo = models.CharField('código', max_length=20, unique=True)
    nombre = models.CharField('nombre', max_length=80)
    ubicacion = models.CharField('ubicación', max_length=120, blank=True)
    observaciones = models.CharField('observaciones', max_length=200, blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'unidad_dental'
        verbose_name = 'Unidad dental'
        verbose_name_plural = 'Unidades dentales'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'

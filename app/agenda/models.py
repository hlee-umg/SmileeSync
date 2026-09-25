from django.db import models


class HorarioDisponibilidad(models.Model):
    """Franja de disponibilidad de un odontólogo."""
    DIAS = [('LUN', 'Lunes'), ('MAR', 'Martes'), ('MIE', 'Miércoles'),
            ('JUE', 'Jueves'), ('VIE', 'Viernes'), ('SAB', 'Sábado')]
    odontologo = models.ForeignKey('catalogo.Odontologo', on_delete=models.CASCADE,
                                   related_name='horarios', verbose_name='odontólogo')
    dia_semana = models.CharField('día de la semana', max_length=3, choices=DIAS)
    hora_inicio = models.TimeField('hora de inicio')
    hora_fin = models.TimeField('hora de fin')
    estado = models.BooleanField('activo', default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'horario_disponibilidad'
        verbose_name = 'Horario de disponibilidad'
        verbose_name_plural = 'Horarios de disponibilidad'


class Cita(models.Model):
    """Cita odontológica programada. Registra tiempos programados y reales."""
    ESTADOS = [('PROGRAMADA', 'Programada'), ('ATENDIDA', 'Atendida'),
               ('CANCELADA', 'Cancelada'), ('REPROGRAMADA', 'Reprogramada')]
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.PROTECT,
                                 related_name='citas', verbose_name='paciente')
    odontologo = models.ForeignKey('catalogo.Odontologo', on_delete=models.PROTECT,
                                   related_name='citas', verbose_name='odontólogo')
    procedimiento = models.ForeignKey('catalogo.Procedimiento', on_delete=models.PROTECT,
                                      related_name='citas', verbose_name='procedimiento')
    # La unidad se asigna automáticamente al programar, tomando la primera
    # libre. Admite nulo por las citas anteriores a la incorporación de las
    # unidades al sistema.
    unidad = models.ForeignKey('catalogo.UnidadDental', on_delete=models.PROTECT,
                               related_name='citas', verbose_name='unidad dental',
                               null=True, blank=True)
    fecha = models.DateField('fecha')
    hora_inicio_programada = models.TimeField('hora inicio programada')
    hora_fin_programada = models.TimeField('hora fin programada')
    hora_inicio_real = models.TimeField('hora inicio real', null=True, blank=True)
    hora_fin_real = models.TimeField('hora fin real', null=True, blank=True)
    duracion_asignada_min = models.PositiveIntegerField('duración asignada (min)')
    duracion_real_min = models.PositiveIntegerField('duración real (min)', null=True, blank=True)
    estado_cita = models.CharField('estado de la cita', max_length=12, choices=ESTADOS, default='PROGRAMADA')
    observaciones = models.TextField('observaciones', blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cita'
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-fecha', 'hora_inicio_programada']

    def __str__(self):
        return f'Cita {self.pk} - {self.fecha}'


class HistorialCita(models.Model):
    """Tabla de histórico/auditoría de la agenda."""
    cita_ref = models.IntegerField('id de cita')
    paciente = models.CharField(max_length=200)
    odontologo = models.CharField(max_length=200)
    fecha_cita = models.DateField()
    estado_cita_anterior = models.CharField(max_length=12)
    accion = models.CharField(max_length=20)
    realizado_por = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_cita'
        verbose_name = 'Historial de cita'
        verbose_name_plural = 'Historial de citas'
        ordering = ['-fecha']


class AusenciaOdontologo(models.Model):
    """Excepción puntual al horario semanal de un odontólogo.

    El patrón de `HorarioDisponibilidad` define la disponibilidad habitual; esta
    tabla registra las fechas concretas en que esa disponibilidad no aplica
    —congreso, vacaciones, una diligencia personal—, ya sea por toda la jornada
    o por una franja. La disponibilidad efectiva de una fecha es el patrón
    semanal menos las ausencias registradas para ella.
    """
    odontologo = models.ForeignKey('catalogo.Odontologo', on_delete=models.CASCADE,
                                   related_name='ausencias', verbose_name='odontólogo')
    fecha = models.DateField('fecha')
    todo_el_dia = models.BooleanField('toda la jornada', default=True)
    hora_inicio = models.TimeField('hora de inicio')
    hora_fin = models.TimeField('hora de finalización')
    motivo = models.CharField('motivo', max_length=200, blank=True)
    registrada_por = models.CharField('registrada por', max_length=150, blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ausencia_odontologo'
        verbose_name = 'Ausencia de odontólogo'
        verbose_name_plural = 'Ausencias de odontólogos'
        ordering = ['-fecha', 'hora_inicio']

    def __str__(self):
        if self.todo_el_dia:
            return f'{self.odontologo} — {self.fecha} (toda la jornada)'
        return (f'{self.odontologo} — {self.fecha} '
                f'{self.hora_inicio:%H:%M} a {self.hora_fin:%H:%M}')

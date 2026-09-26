"""Expediente clínico: odontograma, evolución, plan de tratamiento y cobros.

El módulo de Agenda responde a la pregunta *cuándo* se atiende; este responde a
*qué* se hace y *cómo va*. Está organizado en cuatro piezas que se apoyan unas
en otras:

    Hallazgo        — estado de cada pieza dental (el odontograma).
    NotaClinica     — lo ocurrido en una visita concreta (la evolución).
    PlanTratamiento — el trabajo acordado, dividido en renglones y fases,
                      con su presupuesto.
    Pago            — los abonos aplicados a ese plan.

El plan es además el punto donde el componente predictivo deja de estimar una
cita aislada: cada renglón guarda la duración estimada por el modelo, de modo
que el plan completo puede traducirse en un número de sesiones y en minutos de
sillón antes de agendar la primera.
"""
from decimal import Decimal

from django.db import models

from .piezas import PIEZAS, nombre as nombre_pieza

# Una sesión no debería pasar de dos horas de sillón: las jornadas de la clínica
# son de cuatro horas y un bloque más largo deja al paciente y al profesional sin
# margen. Es el tope con que se reparten los renglones del plan en sesiones.
MINUTOS_SESION_MAX = 120

OPCIONES_PIEZA = [(p, f'{p} — {nombre_pieza(p)}') for p in PIEZAS]


class Hallazgo(models.Model):
    """Estado registrado de una pieza dental en una fecha.

    La tabla es de solo agregado: cada registro es una observación fechada y no
    se modifica. El odontograma vigente es el último hallazgo activo de cada
    combinación de pieza y cara, de modo que el expediente conserva la
    evolución de cada diente sin necesidad de una tabla de auditoría aparte.
    """
    TIPOS = [
        ('SANA', 'Sana'),
        ('CARIES', 'Caries'),
        ('OBTURADA', 'Obturada'),
        ('SELLANTE', 'Sellante'),
        ('ENDODONCIA', 'Endodoncia'),
        ('CORONA', 'Corona'),
        ('PROTESIS', 'Prótesis'),
        ('IMPLANTE', 'Implante'),
        ('FRACTURA', 'Fractura'),
        ('EXTRACCION', 'Indicada para extracción'),
        ('AUSENTE', 'Ausente'),
    ]
    # Hallazgos que describen un problema por atender. Separarlos del resto
    # permite contar la carga pendiente del paciente sin listar estados.
    PATOLOGICOS = {'CARIES', 'FRACTURA', 'EXTRACCION'}
    # Hallazgos que ya son un tratamiento colocado.
    TRATADOS = {'OBTURADA', 'SELLANTE', 'ENDODONCIA', 'CORONA', 'PROTESIS',
                'IMPLANTE'}

    CARAS = [
        ('TODA', 'Toda la pieza'),
        ('O', 'Oclusal / incisal'),
        ('M', 'Mesial'),
        ('D', 'Distal'),
        ('V', 'Vestibular'),
        ('L', 'Lingual / palatina'),
    ]

    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE,
                                 related_name='hallazgos', verbose_name='paciente')
    pieza = models.PositiveSmallIntegerField('pieza dental (FDI)',
                                             choices=OPCIONES_PIEZA)
    cara = models.CharField('cara', max_length=4, choices=CARAS, default='TODA')
    tipo = models.CharField('hallazgo', max_length=12, choices=TIPOS)
    observacion = models.CharField('observación', max_length=200, blank=True)
    nota = models.ForeignKey('clinico.NotaClinica', on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='hallazgos',
                             verbose_name='visita en que se registró')
    fecha = models.DateField('fecha del hallazgo')
    registrado_por = models.CharField('registrado por', max_length=150, blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hallazgo'
        verbose_name = 'Hallazgo odontológico'
        verbose_name_plural = 'Hallazgos odontológicos'
        ordering = ['-fecha', '-creado']

    def __str__(self):
        return f'Pieza {self.pieza} — {self.get_tipo_display()}'

    @property
    def es_patologico(self):
        return self.tipo in self.PATOLOGICOS

    # Abreviatura con que se rotula la pieza en la arcada. El color ya comunica
    # la gravedad; la letra distingue hallazgos del mismo color entre sí.
    SIMBOLOS = {
        'SANA': '·', 'CARIES': 'C', 'OBTURADA': 'O', 'SELLANTE': 'S',
        'ENDODONCIA': 'E', 'CORONA': 'K', 'PROTESIS': 'P', 'IMPLANTE': 'I',
        'FRACTURA': 'F', 'EXTRACCION': 'X', 'AUSENTE': '—',
    }

    @property
    def simbolo(self):
        return self.SIMBOLOS.get(self.tipo, '?')

    @property
    def clase_css(self):
        """Clase de color con que la plantilla pinta la pieza."""
        if self.tipo == 'AUSENTE':
            return 'pieza-ausente'
        if self.tipo in self.PATOLOGICOS:
            return 'pieza-patologica'
        if self.tipo in self.TRATADOS:
            return 'pieza-tratada'
        return 'pieza-sana'


def odontograma_vigente(paciente):
    """Último hallazgo activo de cada pieza y cara del paciente.

    Devuelve {numero_de_pieza: {cara: Hallazgo}}. Al recorrer los registros de
    más antiguo a más reciente, cada escritura sobre la misma clave sustituye a
    la anterior, de modo que al terminar queda la observación vigente.
    """
    vigente = {}
    consulta = (Hallazgo.objects
                .filter(paciente=paciente, estado=True)
                .order_by('fecha', 'creado'))
    for h in consulta:
        vigente.setdefault(h.pieza, {})[h.cara] = h
    return vigente


class NotaClinica(models.Model):
    """Registro de evolución: qué se hizo en una visita.

    Además de documentar la atención, aporta al conjunto de entrenamiento las
    variables que el registro de tiempos no puede conocer por sí solo —número
    de piezas efectivamente tratadas, uso de anestesia y aparición de una
    complicación—, que son las que explican por qué dos citas del mismo
    procedimiento duran distinto.
    """
    cita = models.OneToOneField('agenda.Cita', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='nota',
                                verbose_name='cita atendida')
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.PROTECT,
                                 related_name='notas', verbose_name='paciente')
    odontologo = models.ForeignKey('catalogo.Odontologo', on_delete=models.PROTECT,
                                   related_name='notas', verbose_name='odontólogo')
    fecha = models.DateField('fecha de la visita')
    motivo = models.CharField('motivo de la consulta', max_length=200)
    hallazgos_clinicos = models.TextField('hallazgos clínicos', blank=True)
    procedimiento_realizado = models.TextField('procedimiento realizado')
    piezas_tratadas = models.CharField('piezas tratadas', max_length=120, blank=True,
                                       help_text='Números FDI separados por coma, p. ej. 16, 26.')
    num_piezas = models.PositiveSmallIntegerField('número de piezas tratadas', default=1)
    anestesia = models.BooleanField('se aplicó anestesia', default=False)
    materiales = models.CharField('materiales utilizados', max_length=200, blank=True)
    complicacion = models.BooleanField('hubo complicación', default=False)
    detalle_complicacion = models.CharField('detalle de la complicación',
                                            max_length=200, blank=True)
    indicaciones = models.TextField('indicaciones al paciente', blank=True)
    registrado_por = models.CharField('registrado por', max_length=150, blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nota_clinica'
        verbose_name = 'Nota clínica'
        verbose_name_plural = 'Notas clínicas'
        ordering = ['-fecha', '-creado']

    def __str__(self):
        return f'{self.paciente} — {self.fecha}'

    @property
    def lista_piezas(self):
        return [p.strip() for p in self.piezas_tratadas.split(',') if p.strip()]


class PlanTratamiento(models.Model):
    """Trabajo acordado con el paciente, dividido en renglones y fases.

    Un tratamiento odontológico rara vez cabe en una cita: se diagnostica, se
    presupuesta y se ejecuta en varias sesiones. El plan es el registro de ese
    acuerdo y el que permite responder de antemano cuántas sesiones y cuántos
    minutos de sillón hará falta reservar.
    """
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('APROBADO', 'Aprobado por el paciente'),
        ('EN_CURSO', 'En curso'),
        ('FINALIZADO', 'Finalizado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    ABIERTOS = ('APROBADO', 'EN_CURSO')

    codigo = models.CharField('código', max_length=20, unique=True)
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.PROTECT,
                                 related_name='planes', verbose_name='paciente')
    odontologo = models.ForeignKey('catalogo.Odontologo', on_delete=models.PROTECT,
                                   related_name='planes', verbose_name='odontólogo responsable')
    diagnostico = models.TextField('diagnóstico')
    observaciones = models.TextField('observaciones', blank=True)
    estado_plan = models.CharField('estado del plan', max_length=12,
                                   choices=ESTADOS, default='BORRADOR')
    fecha = models.DateField('fecha de elaboración')
    fecha_aprobacion = models.DateField('fecha de aprobación', null=True, blank=True)
    descuento = models.DecimalField('descuento (Q)', max_digits=10, decimal_places=2,
                                    default=Decimal('0.00'))
    creado_por = models.CharField('elaborado por', max_length=150, blank=True)
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'plan_tratamiento'
        verbose_name = 'Plan de tratamiento'
        verbose_name_plural = 'Planes de tratamiento'
        ordering = ['-fecha', '-creado']

    def __str__(self):
        return f'{self.codigo} — {self.paciente}'

    # ------------------------------------------------------------ presupuesto
    @property
    def renglones(self):
        return self.detalles.filter(estado=True).exclude(estado_detalle='ANULADO')

    @property
    def subtotal(self):
        return sum((d.importe for d in self.renglones), Decimal('0.00'))

    @property
    def total(self):
        return max(Decimal('0.00'), self.subtotal - (self.descuento or Decimal('0.00')))

    @property
    def pagado(self):
        return sum((p.monto for p in self.pagos.filter(estado=True)), Decimal('0.00'))

    @property
    def saldo(self):
        return self.total - self.pagado

    @property
    def esta_pagado(self):
        return self.saldo <= Decimal('0.00')

    # -------------------------------------------------------------- ejecución
    @property
    def minutos_estimados(self):
        """Minutos de sillón que el plan reserva, según el modelo predictivo."""
        return sum(d.duracion_estimada_min for d in self.renglones)

    @property
    def minutos_pendientes(self):
        return sum(d.duracion_estimada_min for d in self.renglones
                   if d.estado_detalle != 'COMPLETADO')

    def sesiones_sugeridas(self):
        """Reparte los renglones pendientes en sesiones de sillón.

        Los renglones se agrupan respetando su fase (una fase posterior no se
        adelanta) y sin que ninguna sesión pase de `MINUTOS_SESION_MAX`. Es una
        estimación de planificación, no una reserva: agendar cada sesión sigue
        siendo una decisión de la recepción.
        """
        sesiones = []
        actual, minutos, fase_actual = [], 0, None
        for d in self.renglones.order_by('fase', 'orden', 'id'):
            if d.estado_detalle == 'COMPLETADO':
                continue
            cambia_fase = fase_actual is not None and d.fase != fase_actual
            no_cabe = minutos + d.duracion_estimada_min > MINUTOS_SESION_MAX
            if actual and (cambia_fase or no_cabe):
                sesiones.append({'fase': fase_actual, 'renglones': actual,
                                 'minutos': minutos})
                actual, minutos = [], 0
            actual.append(d)
            minutos += d.duracion_estimada_min
            fase_actual = d.fase
        if actual:
            sesiones.append({'fase': fase_actual, 'renglones': actual,
                             'minutos': minutos})
        return sesiones

    @property
    def total_renglones(self):
        return self.renglones.count()

    @property
    def renglones_completados(self):
        return self.renglones.filter(estado_detalle='COMPLETADO').count()

    @property
    def avance(self):
        total = self.total_renglones
        return round(self.renglones_completados / total * 100) if total else 0

    def actualizar_avance(self):
        """Mueve el plan a EN_CURSO o FINALIZADO según sus renglones.

        Se invoca al cerrar una cita ligada al plan, de modo que el estado no
        dependa de que alguien lo cambie a mano.
        """
        if self.estado_plan not in self.ABIERTOS:
            return self.estado_plan
        total = self.total_renglones
        completados = self.renglones_completados
        nuevo = self.estado_plan
        if total and completados == total:
            nuevo = 'FINALIZADO'
        elif completados:
            nuevo = 'EN_CURSO'
        if nuevo != self.estado_plan:
            self.estado_plan = nuevo
            self.save(update_fields=['estado_plan'])
        return nuevo

    @classmethod
    def siguiente_codigo(cls):
        """Siguiente código libre de la serie PLAN-0000.

        Parte del último identificador y avanza hasta encontrar uno sin usar,
        de modo que convivan los planes creados desde la pantalla con los que
        el seed siembra con un código fijo.
        """
        ultimo = cls.objects.order_by('-id').first()
        numero = (ultimo.pk if ultimo else 0) + 1
        while cls.objects.filter(codigo=f'PLAN-{numero:04d}').exists():
            numero += 1
        return f'PLAN-{numero:04d}'


class DetallePlan(models.Model):
    """Renglón del plan: un procedimiento sobre una pieza, con su precio.

    `duracion_estimada_min` se toma del servicio de estimación en el momento de
    agregar el renglón y se conserva: es la cifra con la que se presupuestó el
    tiempo, y compararla después con la duración real es lo que permite medir
    al modelo sobre tratamientos completos y no solo sobre citas sueltas.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('AGENDADO', 'Agendado'),
        ('COMPLETADO', 'Completado'),
        ('ANULADO', 'Anulado'),
    ]
    plan = models.ForeignKey(PlanTratamiento, on_delete=models.CASCADE,
                             related_name='detalles', verbose_name='plan')
    fase = models.PositiveSmallIntegerField('fase', default=1,
                                            help_text='Las fases se ejecutan en orden.')
    orden = models.PositiveSmallIntegerField('orden dentro de la fase', default=1)
    procedimiento = models.ForeignKey('catalogo.Procedimiento', on_delete=models.PROTECT,
                                      related_name='renglones_plan',
                                      verbose_name='procedimiento')
    pieza = models.PositiveSmallIntegerField('pieza dental', null=True, blank=True,
                                             choices=OPCIONES_PIEZA)
    num_piezas = models.PositiveSmallIntegerField('número de piezas', default=1)
    precio_unitario = models.DecimalField('precio unitario (Q)', max_digits=10,
                                          decimal_places=2, default=Decimal('0.00'))
    duracion_estimada_min = models.PositiveIntegerField('duración estimada (min)', default=0)
    origen_estimacion = models.CharField('origen de la estimación', max_length=12, blank=True)
    estado_detalle = models.CharField('estado', max_length=10, choices=ESTADOS,
                                      default='PENDIENTE')
    cita = models.ForeignKey('agenda.Cita', on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='renglones_plan',
                             verbose_name='cita que lo atiende')
    estado = models.BooleanField('activo', default=True)  # borrado lógico
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'detalle_plan'
        verbose_name = 'Renglón del plan'
        verbose_name_plural = 'Renglones del plan'
        ordering = ['fase', 'orden', 'id']

    def __str__(self):
        if self.pieza:
            return f'{self.procedimiento.nombre} — pieza {self.pieza}'
        return self.procedimiento.nombre

    @property
    def importe(self):
        return (self.precio_unitario or Decimal('0.00')) * self.num_piezas

    @property
    def etiqueta_origen(self):
        return {'modelo': 'Modelo predictivo',
                'historico': 'Promedio histórico',
                'catalogo': 'Catálogo'}.get(self.origen_estimacion, '—')


class Pago(models.Model):
    """Abono aplicado a un plan de tratamiento.

    En la clínica el tratamiento se liquida por abonos, no en un solo pago, de
    modo que el saldo se obtiene restando los abonos vigentes del total del
    plan. Un abono mal registrado se anula lógicamente; no se elimina, para que
    el estado de cuenta conserve la traza.
    """
    METODOS = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
    ]
    plan = models.ForeignKey(PlanTratamiento, on_delete=models.PROTECT,
                             related_name='pagos', verbose_name='plan')
    fecha = models.DateField('fecha del abono')
    monto = models.DecimalField('monto (Q)', max_digits=10, decimal_places=2)
    metodo = models.CharField('forma de pago', max_length=14, choices=METODOS,
                              default='EFECTIVO')
    referencia = models.CharField('referencia o número de recibo', max_length=60, blank=True)
    observaciones = models.CharField('observaciones', max_length=200, blank=True)
    recibido_por = models.CharField('recibido por', max_length=150, blank=True)
    estado = models.BooleanField('vigente', default=True)  # anulación lógica
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pago'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha', '-creado']

    def __str__(self):
        return f'Q{self.monto} — {self.plan.codigo}'


class HistorialPlan(models.Model):
    """Tabla de histórico/auditoría del expediente clínico.

    Sigue la convención del resto del sistema: referencias por identificador
    entero, sin llave foránea, para que el histórico sobreviva al registro que
    describe.
    """
    ACCIONES = [
        ('CREACION', 'Creación'),
        ('ACTUALIZACION', 'Actualización'),
        ('APROBACION', 'Aprobación'),
        ('RECHAZO', 'Rechazo'),
        ('FINALIZACION', 'Finalización'),
        ('ANULACION', 'Anulación'),
        ('PAGO', 'Registro de pago'),
    ]
    plan_ref = models.IntegerField('id del plan')
    codigo = models.CharField(max_length=20)
    paciente = models.CharField(max_length=200)
    estado_anterior = models.CharField(max_length=12, blank=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    detalle = models.CharField(max_length=200, blank=True)
    realizado_por = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_plan'
        verbose_name = 'Historial de plan'
        verbose_name_plural = 'Historial de planes'
        ordering = ['-fecha']

    @classmethod
    def registrar(cls, plan, accion, realizado_por, detalle='', estado_anterior=None):
        return cls.objects.create(
            plan_ref=plan.pk, codigo=plan.codigo, paciente=str(plan.paciente),
            estado_anterior=(estado_anterior if estado_anterior is not None
                             else plan.estado_plan),
            accion=accion, detalle=detalle, realizado_por=realizado_por)

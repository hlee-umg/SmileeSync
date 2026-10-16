"""Cálculo de los indicadores y las series que alimentan los reportes.

Se mantiene separado de las vistas porque las mismas cifras las consumen la
pantalla de reportes y, a futuro, la exportación. Todas las consultas parten de
las citas vigentes y excluyen las canceladas, que no representan atención
prestada ni tiempo de sillón ocupado.
"""
from datetime import timedelta

from django.db.models import Avg, Count, F, Sum
from django.utils import timezone

from agenda.disponibilidad import capacidad_minutos
from agenda.models import Cita
from catalogo.models import Odontologo, Procedimiento

MINIMO_PARA_PROMEDIO = 3


def _dias_habiles(desde, hasta):
    dias, actual = [], desde
    while actual <= hasta:
        if actual.weekday() < 6:
            dias.append(actual)
        actual += timedelta(days=1)
    return dias


def rango(semanas=8):
    """Período que abarcan los reportes: las últimas semanas cerradas."""
    hoy = timezone.localdate()
    desde = hoy - timedelta(weeks=semanas)
    return desde, hoy


def resumen(desde, hasta):
    """Cifras globales del período."""
    citas = Cita.objects.filter(fecha__range=(desde, hasta), estado=True)
    atendidas = citas.filter(estado_cita='ATENDIDA')
    canceladas = citas.filter(estado_cita='CANCELADA')

    minutos = atendidas.aggregate(t=Sum('duracion_real_min'))['t'] or 0
    capacidad = capacidad_minutos(list(Odontologo.objects.filter(estado=True)),
                                  _dias_habiles(desde, hasta))
    medidas = atendidas.filter(duracion_real_min__isnull=False)
    desvio = medidas.aggregate(
        real=Avg('duracion_real_min'), asignado=Avg('duracion_asignada_min'),
        total=Count('id'))

    mae = None
    if desvio['total']:
        suma = sum(abs(c.duracion_real_min - c.duracion_asignada_min)
                   for c in medidas.only('duracion_real_min', 'duracion_asignada_min'))
        mae = round(suma / desvio['total'], 1)

    return {
        'total': citas.count(),
        'atendidas': atendidas.count(),
        'canceladas': canceladas.count(),
        'tasa_cancelacion': round(canceladas.count() / citas.count() * 100, 1)
                            if citas.count() else 0,
        'horas_sillon': round(minutos / 60, 1),
        'utilizacion': round(minutos / capacidad * 100, 1) if capacidad else 0,
        'promedio_real': round(desvio['real'] or 0, 1),
        'promedio_asignado': round(desvio['asignado'] or 0, 1),
        'mae': mae,
        'medidas': desvio['total'] or 0,
    }


def atenciones_por_semana(desde, hasta):
    """Serie semanal de citas atendidas y canceladas."""
    etiquetas, atendidas, canceladas = [], [], []
    inicio = desde - timedelta(days=desde.weekday())
    while inicio <= hasta:
        fin = inicio + timedelta(days=6)
        base = Cita.objects.filter(fecha__range=(inicio, fin), estado=True)
        etiquetas.append(inicio.strftime('%d/%m'))
        atendidas.append(base.filter(estado_cita='ATENDIDA').count())
        canceladas.append(base.filter(estado_cita='CANCELADA').count())
        inicio = fin + timedelta(days=1)
    return {'etiquetas': etiquetas, 'atendidas': atendidas,
            'canceladas': canceladas}


def carga_por_odontologo(desde, hasta):
    """Horas de sillón y número de atenciones por profesional."""
    filas = []
    for odo in Odontologo.objects.filter(estado=True).order_by('apellidos'):
        base = Cita.objects.filter(odontologo=odo, fecha__range=(desde, hasta),
                                   estado=True, estado_cita='ATENDIDA')
        minutos = base.aggregate(t=Sum('duracion_real_min'))['t'] or 0
        capacidad = capacidad_minutos([odo], _dias_habiles(desde, hasta))
        filas.append({
            'odontologo': str(odo),
            'especialidad': odo.especialidad.nombre,
            'atenciones': base.count(),
            'horas': round(minutos / 60, 1),
            'utilizacion': round(minutos / capacidad * 100, 1) if capacidad else 0,
        })
    return filas


def procedimientos_frecuentes(desde, hasta, limite=8):
    """Procedimientos más realizados en el período."""
    base = (Cita.objects
            .filter(fecha__range=(desde, hasta), estado=True,
                    estado_cita='ATENDIDA')
            .values('procedimiento__nombre')
            .annotate(veces=Count('id'), minutos=Sum('duracion_real_min'))
            .order_by('-veces')[:limite])
    return [{'nombre': r['procedimiento__nombre'], 'veces': r['veces'],
             'horas': round((r['minutos'] or 0) / 60, 1)} for r in base]


def precision_por_procedimiento(desde, hasta):
    """Contraste entre la duración del catálogo, la asignada y la real.

    Es la cifra que sustenta el componente predictivo: muestra en qué
    procedimientos la duración de referencia se aleja de lo que la clínica
    tarda realmente, que son aquellos donde la estimación aporta más.
    """
    filas = []
    for proc in Procedimiento.objects.filter(estado=True).order_by('nombre'):
        base = Cita.objects.filter(
            procedimiento=proc, fecha__range=(desde, hasta), estado=True,
            estado_cita='ATENDIDA', duracion_real_min__isnull=False)
        n = base.count()
        if n < MINIMO_PARA_PROMEDIO:
            continue
        agregado = base.aggregate(real=Avg('duracion_real_min'),
                                  asignado=Avg('duracion_asignada_min'))
        real = round(agregado['real'], 1)
        catalogo = proc.duracion_promedio_min
        filas.append({
            'nombre': proc.nombre,
            'catalogo': catalogo,
            'asignado': round(agregado['asignado'], 1),
            'real': real,
            'desvio': round(real - catalogo, 1),
            'desvio_pct': round((real - catalogo) / catalogo * 100, 1) if catalogo else 0,
            'atenciones': n,
        })
    return sorted(filas, key=lambda f: abs(f['desvio_pct']), reverse=True)


def ocupacion_por_hora(desde, hasta):
    """Distribución de las atenciones a lo largo de la jornada."""
    horas = list(range(7, 19))
    conteo = {h: 0 for h in horas}
    for c in Cita.objects.filter(fecha__range=(desde, hasta), estado=True,
                                 estado_cita='ATENDIDA').only(
            'hora_inicio_programada'):
        h = c.hora_inicio_programada.hour
        if h in conteo:
            conteo[h] += 1
    return {'etiquetas': [f'{h:02d}:00' for h in horas],
            'valores': [conteo[h] for h in horas]}

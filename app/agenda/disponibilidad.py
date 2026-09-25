"""Disponibilidad efectiva de la clínica: horarios, ausencias y unidades.

Tres partes del sistema necesitan saber si un espacio está libre: la validación
al programar una cita, la recomendación de bloques sobre el calendario y el
indicador de utilización de la agenda. Cuando cada una resolvía esa pregunta
por su cuenta bastaba un cambio en una para que las tres dejaran de coincidir,
de modo que aquí se concentra el criterio y las tres lo consumen.

Dos recursos limitan la operación y deben cumplirse a la vez:

* el **odontólogo**, cuya disponibilidad es su patrón semanal menos las
  ausencias registradas para esa fecha concreta;
* la **unidad dental**, de la que la clínica tiene menos ejemplares que
  profesionales, por lo que dos odontólogos libres no implican dos citas
  simultáneas posibles.
"""
from datetime import date, datetime, timedelta

DIAS = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']

# Granularidad con que se recorre la jornada para medir la capacidad.
PASO_CAPACIDAD_MIN = 15


def _a_minutos(hora):
    return hora.hour * 60 + hora.minute


def _a_hora(minutos):
    minutos = max(0, min(24 * 60 - 1, minutos))
    return datetime.min.time().replace(hour=minutos // 60, minute=minutos % 60)


def hay_traslape(inicio_a, fin_a, inicio_b, fin_b):
    """Dos intervalos se traslapan si cada uno empieza antes de que el otro termine."""
    return inicio_a < fin_b and inicio_b < fin_a


def _restar(intervalos, quitar):
    """Resta un intervalo de una lista de intervalos, en minutos.

    Un corte en medio parte el intervalo en dos, y un corte que lo cubre por
    completo lo elimina.
    """
    inicio_q, fin_q = quitar
    resultado = []
    for inicio, fin in intervalos:
        if fin_q <= inicio or inicio_q >= fin:      # no se tocan
            resultado.append((inicio, fin))
            continue
        if inicio_q > inicio:                        # queda un tramo antes
            resultado.append((inicio, inicio_q))
        if fin_q < fin:                              # queda un tramo después
            resultado.append((fin_q, fin))
    return resultado


def franjas_efectivas(odontologo, fecha):
    """Intervalos (hora_inicio, hora_fin) en que el odontólogo atiende esa fecha.

    Parte del patrón semanal y le resta las ausencias registradas para el día.
    """
    from .models import AusenciaOdontologo, HorarioDisponibilidad

    intervalos = [
        (_a_minutos(f.hora_inicio), _a_minutos(f.hora_fin))
        for f in HorarioDisponibilidad.objects.filter(
            odontologo=odontologo, dia_semana=DIAS[fecha.weekday()], estado=True)
        if f.hora_fin > f.hora_inicio
    ]
    if not intervalos:
        return []

    for ausencia in AusenciaOdontologo.objects.filter(
            odontologo=odontologo, fecha=fecha, estado=True):
        intervalos = _restar(intervalos, (_a_minutos(ausencia.hora_inicio),
                                          _a_minutos(ausencia.hora_fin)))
        if not intervalos:
            break

    return [(_a_hora(i), _a_hora(f)) for i, f in sorted(intervalos)]


def cabe_en_franja(odontologo, fecha, inicio, fin):
    """La cita completa cabe dentro de una sola franja efectiva."""
    return any(f_ini <= inicio and fin <= f_fin
               for f_ini, f_fin in franjas_efectivas(odontologo, fecha))


def unidades_activas():
    from catalogo.models import UnidadDental
    return list(UnidadDental.objects.filter(estado=True).order_by('codigo'))


def unidades_libres(fecha, inicio, fin, excluir_cita=None):
    """Unidades dentales sin ocupar en ese intervalo.

    La capacidad se deriva de las unidades dadas de alta, de modo que agregar
    un sillón nuevo es un registro más en el catálogo y el sistema se ajusta
    sin tocar el código.
    """
    from .models import Cita

    ocupadas = set()
    citas = (Cita.objects.filter(fecha=fecha, estado=True, unidad__isnull=False)
             .exclude(estado_cita='CANCELADA'))
    if excluir_cita:
        citas = citas.exclude(pk=excluir_cita)
    for cita in citas:
        if hay_traslape(inicio, fin, cita.hora_inicio_programada,
                        cita.hora_fin_programada):
            ocupadas.add(cita.unidad_id)

    return [u for u in unidades_activas() if u.pk not in ocupadas]


def asignar_unidad(fecha, inicio, fin, excluir_cita=None):
    """Primera unidad libre del intervalo, o None si están todas ocupadas."""
    libres = unidades_libres(fecha, inicio, fin, excluir_cita)
    return libres[0] if libres else None


def capacidad_minutos(odontologos, fechas):
    """Minutos de atención realmente posibles en el período.

    En cada intervalo la capacidad es el menor entre los odontólogos
    disponibles y las unidades dentales activas: de nada sirve que haya tres
    profesionales libres si la clínica solo tiene dos sillones. Medir contra
    las horas declaradas por los odontólogos sobrestimaría la capacidad y
    haría que la utilización se reportara por debajo de la real.
    """
    unidades = len(unidades_activas())
    if not unidades:
        return 0

    # Franjas efectivas de cada odontólogo, por fecha, en minutos.
    por_fecha = {}
    for f in fechas:
        por_fecha[f] = [
            [(_a_minutos(i), _a_minutos(t)) for i, t in franjas_efectivas(o, f)]
            for o in odontologos
        ]

    total = 0
    for f, listas in por_fecha.items():
        if not listas:
            continue
        inicio_dia = min((i for lista in listas for i, _ in lista), default=None)
        fin_dia = max((t for lista in listas for _, t in lista), default=None)
        if inicio_dia is None:
            continue
        momento = inicio_dia
        while momento < fin_dia:
            disponibles = sum(
                1 for lista in listas
                if any(i <= momento < t for i, t in lista))
            total += min(disponibles, unidades) * PASO_CAPACIDAD_MIN
            momento += PASO_CAPACIDAD_MIN
    return total

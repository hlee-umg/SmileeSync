"""Servicio de estimación de duración de procedimientos.

Este módulo es el punto de integración del componente predictivo con el resto
del sistema. Aplica una cadena de respaldo de tres niveles, de modo que la
agenda siempre obtiene una estimación utilizable aunque el modelo de
aprendizaje automático todavía no esté entrenado:

    1. MODELO    — si existe una versión activa del modelo entrenado, se usa.
    2. HISTÓRICO — si no, se promedia la duración real de las citas ya
                   atendidas de ese mismo procedimiento (y odontólogo, si hay
                   suficientes registros).
    3. CATÁLOGO  — si tampoco hay historial, se usa la duración promedio
                   declarada en el catálogo.

La estimación mejora sola conforme la clínica acumula citas atendidas.
"""
import os
from dataclasses import dataclass

from django.db.models import Avg, Count

DIAS = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']

MINIMO_REGISTROS_HISTORICOS = 3   # por debajo de esto el promedio no es fiable
REDONDEO_MIN = 5                  # las citas se agendan en múltiplos de 5 minutos


@dataclass
class Estimacion:
    """Resultado de una estimación de duración."""
    duracion_min: int
    bloque_min: int
    bloque_max: int
    origen: str          # 'modelo' | 'historico' | 'catalogo'
    detalle: str         # texto explicativo para mostrar al usuario
    modelo = None        # instancia de ModeloVersion cuando el origen es 'modelo'

    @property
    def etiqueta_origen(self):
        return {
            'modelo': 'Modelo predictivo',
            'historico': 'Promedio histórico de la clínica',
            'catalogo': 'Duración de referencia del catálogo',
        }.get(self.origen, self.origen)


def _redondear(minutos):
    """Redondea al múltiplo de 5 más cercano, con un mínimo de 10 minutos."""
    return max(10, int(round(minutos / REDONDEO_MIN) * REDONDEO_MIN))


def _bloque_recomendado(duracion):
    """Un rango alrededor de la estimación: el mínimo para no quedarse corto y
    el máximo para no bloquear agenda de más."""
    return _redondear(duracion * 0.85), _redondear(duracion * 1.20)


def _modelo_activo():
    from .models import ModeloVersion
    return ModeloVersion.objects.filter(activo=True, estado=True).first()


# ──────────────────────────── caché del modelo ────────────────────────────
# El archivo del modelo puede pesar varios megabytes. Deserializarlo en cada
# estimación significaría releerlo en cada cita que se agenda, de modo que se
# conserva en memoria y solo se recarga cuando cambia la versión activa.
_CACHE = {'version': None, 'estimador': None, 'anestesia': {}}


def limpiar_cache():
    """Descarta el modelo en memoria. Se invoca al activar otra versión."""
    _CACHE['version'] = None
    _CACHE['estimador'] = None
    _CACHE['anestesia'] = {}


def _cargar(modelo):
    """Devuelve el estimador de la versión indicada, cargándolo una sola vez."""
    if _CACHE['version'] == modelo.pk and _CACHE['estimador'] is not None:
        return _CACHE['estimador']
    try:
        import joblib
    except ImportError:
        return None
    if not modelo.ruta_archivo or not os.path.exists(modelo.ruta_archivo):
        return None
    try:
        estimador = joblib.load(modelo.ruta_archivo)
    except Exception:
        # Un archivo dañado o entrenado con otra versión de la biblioteca no
        # debe impedir que se agende: la cadena de respaldo continúa.
        return None
    _CACHE['version'] = modelo.pk
    _CACHE['estimador'] = estimador
    return estimador


def _anestesia_habitual(procedimiento):
    """Proporción histórica de atenciones de ese procedimiento con anestesia.

    En el momento de agendar no se sabe si se aplicará anestesia, de modo que se
    usa el comportamiento habitual del procedimiento. La complicación, en
    cambio, se asume ausente: por definición es imprevista, y el sistema estima
    el caso nominal.
    """
    if procedimiento.pk in _CACHE['anestesia']:
        return _CACHE['anestesia'][procedimiento.pk]
    from clinico.models import NotaClinica
    notas = NotaClinica.objects.filter(cita__procedimiento=procedimiento,
                                       estado=True)
    total = notas.count()
    valor = 1 if total and notas.filter(anestesia=True).count() * 2 >= total else 0
    _CACHE['anestesia'][procedimiento.pk] = valor
    return valor


def _estimar_con_modelo(modelo, procedimiento, odontologo, fecha, hora, num_piezas):
    """Carga el modelo entrenado y predice la duración.

    Mientras el archivo serializado no exista o las bibliotecas de aprendizaje
    automático no estén instaladas en el servidor, devuelve None para que la
    cadena de respaldo continúe con el promedio histórico.
    """
    estimador = _cargar(modelo)
    if estimador is None:
        return None
    try:
        import pandas as pd
    except ImportError:
        return None

    try:
        # Los nombres de las columnas deben coincidir con los del entrenamiento.
        entrada = pd.DataFrame([{
            'procedimiento': procedimiento.nombre,
            'odontologo': f'{odontologo.nombres} {odontologo.apellidos}',
            'dia_semana': DIAS[fecha.weekday()],
            'hora_inicio': hora.hour,
            'num_piezas': num_piezas,
            'anestesia': _anestesia_habitual(procedimiento),
            'complicacion': 0,
        }])
        return float(estimador.predict(entrada)[0])
    except Exception:
        # Un fallo del modelo no debe impedir agendar una cita.
        return None


def _estimar_con_historico(procedimiento, odontologo):
    """Promedio de la duración real de las citas atendidas de ese procedimiento.

    Si hay suficientes registros del mismo odontólogo se prefiere ese promedio,
    porque el ritmo de trabajo varía entre profesionales.
    """
    from agenda.models import Cita

    base = Cita.objects.filter(
        procedimiento=procedimiento,
        estado_cita='ATENDIDA',
        duracion_real_min__isnull=False,
        estado=True,
    )

    del_odontologo = base.filter(odontologo=odontologo).aggregate(
        promedio=Avg('duracion_real_min'), total=Count('id'))
    if (del_odontologo['total'] or 0) >= MINIMO_REGISTROS_HISTORICOS:
        return del_odontologo['promedio'], del_odontologo['total'], True

    general = base.aggregate(promedio=Avg('duracion_real_min'), total=Count('id'))
    if (general['total'] or 0) >= MINIMO_REGISTROS_HISTORICOS:
        return general['promedio'], general['total'], False

    return None, 0, False


def estimar_duracion(procedimiento, odontologo, fecha, hora, num_piezas=1):
    """Estima la duración de un procedimiento y el bloque de tiempo sugerido."""
    # --- Nivel 1: modelo predictivo entrenado ---
    modelo = _modelo_activo()
    if modelo:
        prediccion = _estimar_con_modelo(modelo, procedimiento, odontologo,
                                         fecha, hora, num_piezas)
        if prediccion:
            duracion = _redondear(prediccion)
            minimo, maximo = _bloque_recomendado(duracion)
            est = Estimacion(duracion, minimo, maximo, 'modelo',
                             f'Estimado por {modelo.nombre} '
                             f'({modelo.get_algoritmo_display()}).')
            est.modelo = modelo
            return est

    # --- Nivel 2: promedio histórico real de la clínica ---
    promedio, total, es_del_odontologo = _estimar_con_historico(procedimiento, odontologo)
    if promedio:
        duracion = _redondear(promedio)
        minimo, maximo = _bloque_recomendado(duracion)
        alcance = ('de este odontólogo' if es_del_odontologo
                   else 'de todos los odontólogos')
        return Estimacion(duracion, minimo, maximo, 'historico',
                          f'Promedio de {total} atenciones previas {alcance}. '
                          f'La precisión aumentará al acumularse más registros.')

    # --- Nivel 3: duración de referencia del catálogo ---
    duracion = _redondear(procedimiento.duracion_promedio_min)
    minimo, maximo = _bloque_recomendado(duracion)
    return Estimacion(duracion, minimo, maximo, 'catalogo',
                      'Aún no hay suficientes atenciones registradas de este '
                      'procedimiento; se usa la duración de referencia del catálogo.')


def registrar_prediccion(cita, estimacion):
    """Guarda la predicción generada para poder contrastarla después con la
    duración real. Solo se registra cuando proviene de un modelo entrenado,
    porque la tabla de predicciones exige una versión de modelo asociada."""
    if estimacion.origen != 'modelo' or not estimacion.modelo:
        return None
    from .models import Prediccion
    return Prediccion.objects.create(
        cita=cita,
        modelo=estimacion.modelo,
        duracion_estimada_min=estimacion.duracion_min,
        bloque_min_recomendado=estimacion.bloque_min,
        bloque_max_recomendado=estimacion.bloque_max,
    )


def registrar_dato_entrenamiento(cita):
    """Incorpora una cita atendida al conjunto de entrenamiento del modelo.

    Se invoca al registrar los tiempos reales. Es idempotente: si la atención
    ya estaba en el conjunto —porque se corrigió la hora o porque la nota
    clínica se escribió después— actualiza la fila en lugar de duplicarla.
    """
    from .entrenamiento import _fila_de
    from .models import DatoEntrenamiento

    if not cita.duracion_real_min:
        return None
    dato, _ = DatoEntrenamiento.objects.update_or_create(
        cita=cita, defaults=_fila_de(cita))
    return dato

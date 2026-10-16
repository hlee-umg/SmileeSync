"""Entrenamiento del modelo de estimación de duraciones.

Este módulo se ejecuta **fuera del proceso web**. La razón no es el costo de
cómputo —entrenar sobre unos cientos de registros toma menos de un segundo—
sino la memoria: importar scikit-learn y pandas añade alrededor de 170 MB al
proceso que lo haga, y el servidor de la clínica dispone de 2 GB compartidos
entre PostgreSQL y los procesos de Gunicorn. Mantener el entrenamiento en un
comando aparte evita cargar esas bibliotecas en los procesos que atienden
peticiones.

El resultado es un archivo serializado y un registro de versión con sus
métricas. El proceso web únicamente carga ese archivo y predice.
"""
import os
from dataclasses import dataclass, field
from datetime import datetime

from django.conf import settings
from django.utils import timezone

DIAS = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']

# Por debajo de este número de atenciones el modelo no se considera fiable y la
# estimación sigue recayendo en el promedio histórico o en el catálogo.
MINIMO_REGISTROS = 60

# Proporción del conjunto que se reserva para evaluar. No se entrena con ella.
PROPORCION_PRUEBA = 0.25

# Meta declarada en la hipótesis del proyecto: el modelo debe reducir al menos
# en este porcentaje el error de estimar con la duración del catálogo.
META_REDUCCION_PCT = 25.0

# Columnas de la tabla del conjunto que describen cada atención.
CAMPOS = ['tipo_procedimiento', 'odontologo', 'dia_semana', 'hora_inicio',
          'num_piezas', 'anestesia', 'complicacion', 'duracion_catalogo_min',
          'duracion_real_min']

CATEGORICAS = ['procedimiento', 'odontologo', 'dia_semana']
NUMERICAS = ['hora_inicio', 'num_piezas', 'anestesia', 'complicacion']

ALGORITMOS = {
    'LINEAL': 'Regresión lineal múltiple',
    'RF': 'Random Forest',
}


@dataclass
class Resultado:
    algoritmo: str
    mae: float
    rmse: float
    r2: float
    registros: int
    registros_prueba: int
    mae_base: float
    mae_catalogo: float = 0.0
    ruta: str = ''
    tamano_kb: float = 0.0
    segundos: float = 0.0
    importancias: list = field(default_factory=list)

    @property
    def mejora_pct(self):
        """Reducción del error frente a estimar siempre el promedio global."""
        if not self.mae_base:
            return 0.0
        return round((self.mae_base - self.mae) / self.mae_base * 100, 1)

    @property
    def mejora_catalogo_pct(self):
        """Reducción del error frente a la duración de referencia del catálogo.

        Es la cifra con que se resuelve la hipótesis del proyecto, porque el
        catálogo es el método de bloques fijos que la clínica emplea hoy. Se
        mide sobre el mismo subconjunto de prueba con que se evalúa el modelo.
        """
        if not self.mae_catalogo:
            return 0.0
        return round((self.mae_catalogo - self.mae) / self.mae_catalogo * 100, 1)

    @property
    def cumple_meta(self):
        """La meta del proyecto: reducir al menos un 25 % el error del catálogo."""
        return self.mejora_catalogo_pct >= META_REDUCCION_PCT


def directorio_modelos():
    ruta = os.path.join(settings.BASE_DIR, 'modelos')
    os.makedirs(ruta, exist_ok=True)
    return ruta


def _fila_de(cita):
    """Valores con que una atención concluida entra al conjunto.

    Las variables provienen de dos fuentes. La cita aporta el procedimiento, el
    profesional, el día y la hora; la nota clínica de la visita aporta el número
    de piezas tratadas, el uso de anestesia y la aparición de complicaciones,
    que son las que explican por qué dos atenciones del mismo procedimiento no
    duran lo mismo. Cuando la visita no fue documentada se asumen los valores
    por omisión, de modo que la falta de nota no excluya el registro.
    """
    nota = getattr(cita, 'nota', None)
    return {
        'tipo_procedimiento': cita.procedimiento.nombre,
        'odontologo': f'{cita.odontologo.nombres} {cita.odontologo.apellidos}',
        'dia_semana': DIAS[cita.fecha.weekday()],
        'hora_inicio': cita.hora_inicio_programada.hour,
        'num_piezas': nota.num_piezas if nota else 1,
        'anestesia': bool(nota.anestesia) if nota else False,
        'complicacion': bool(nota.complicacion) if nota else False,
        'duracion_catalogo_min': cita.procedimiento.duracion_promedio_min,
        'duracion_real_min': cita.duracion_real_min,
    }


def _citas_aptas():
    from agenda.models import Cita
    return (Cita.objects
            .filter(estado_cita='ATENDIDA', duracion_real_min__isnull=False,
                    estado=True)
            .select_related('procedimiento', 'odontologo', 'nota'))


def sincronizar():
    """Pone al día el conjunto de entrenamiento con las atenciones vigentes.

    Da de alta las que falten, corrige las que cambiaron después de
    registrarse —una duración real que se rectifica, una nota que se escribe
    más tarde— y da de baja las que dejaron de ser válidas, como una cita que
    se canceló después de haberse atendido. Devuelve (altas, cambios, bajas).
    """
    from .models import DatoEntrenamiento

    aptas = {c.pk: _fila_de(c) for c in _citas_aptas()}
    existentes = {d.cita_id: d for d in DatoEntrenamiento.objects.all()
                  if d.cita_id}

    altas = [DatoEntrenamiento(cita_id=pk, **fila)
             for pk, fila in aptas.items() if pk not in existentes]
    if altas:
        DatoEntrenamiento.objects.bulk_create(altas, batch_size=500)

    cambios = []
    for pk, fila in aptas.items():
        dato = existentes.get(pk)
        if dato is None:
            continue
        distintos = [c for c, v in fila.items() if getattr(dato, c) != v]
        if distintos:
            for campo in distintos:
                setattr(dato, campo, fila[campo])
            cambios.append(dato)
    if cambios:
        DatoEntrenamiento.objects.bulk_update(cambios, CAMPOS, batch_size=500)

    sobrantes = [d.pk for pk, d in existentes.items() if pk not in aptas]
    if sobrantes:
        DatoEntrenamiento.objects.filter(pk__in=sobrantes).delete()

    return len(altas), len(cambios), len(sobrantes)


def reunir_datos(sincronizado=True):
    """Devuelve el conjunto de entrenamiento como lista de registros.

    Lee la tabla del conjunto, que es la que deja constancia de con qué datos
    se entrenó cada versión. Por omisión la pone al día antes de leerla, para
    que un entrenamiento manual nunca opere sobre un conjunto rezagado.
    """
    from .models import DatoEntrenamiento

    if sincronizado:
        sincronizar()

    return [{
        'procedimiento': d.tipo_procedimiento,
        'odontologo': d.odontologo,
        'dia_semana': d.dia_semana,
        'hora_inicio': d.hora_inicio,
        'num_piezas': d.num_piezas,
        'anestesia': int(d.anestesia),
        'complicacion': int(d.complicacion),
        'duracion_catalogo': d.duracion_catalogo_min,
        'duracion_real_min': d.duracion_real_min,
    } for d in DatoEntrenamiento.objects.all().order_by('pk')]


def _construir(algoritmo):
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    preparacion = ColumnTransformer([
        ('categoricas', OneHotEncoder(handle_unknown='ignore'), CATEGORICAS),
        ('numericas', 'passthrough', NUMERICAS),
    ])
    if algoritmo == 'RF':
        estimador = RandomForestRegressor(
            n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=1)
    else:
        estimador = LinearRegression()
    return Pipeline([('preparacion', preparacion), ('estimador', estimador)])


def entrenar(algoritmo='RF', guardar=True):
    """Entrena una versión del modelo y devuelve sus métricas.

    Devuelve None cuando no hay registros suficientes, para que quien invoque
    pueda informarlo sin tratarlo como un error.
    """
    import time

    import joblib
    import pandas as pd
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split

    filas = reunir_datos()
    if len(filas) < MINIMO_REGISTROS:
        return None

    df = pd.DataFrame(filas)
    # La duración del catálogo no es una variable del modelo: se arrastra para
    # medir contra ella en el mismo subconjunto de prueba.
    catalogo = df['duracion_catalogo']
    X = df.drop(columns=['duracion_real_min', 'duracion_catalogo'])
    y = df['duracion_real_min']
    X_ent, X_pru, y_ent, y_pru, _, cat_pru = train_test_split(
        X, y, catalogo, test_size=PROPORCION_PRUEBA, random_state=42)

    pipe = _construir(algoritmo)
    inicio = time.perf_counter()
    pipe.fit(X_ent, y_ent)
    segundos = time.perf_counter() - inicio

    prediccion = pipe.predict(X_pru)
    # Línea base: estimar siempre el promedio global. Es contra lo que se mide
    # si el modelo aporta algo.
    base = [y_ent.mean()] * len(y_pru)

    resultado = Resultado(
        algoritmo=algoritmo,
        mae=round(float(mean_absolute_error(y_pru, prediccion)), 2),
        rmse=round(float(mean_squared_error(y_pru, prediccion) ** 0.5), 2),
        r2=round(float(r2_score(y_pru, prediccion)), 3),
        registros=len(df),
        registros_prueba=len(y_pru),
        mae_base=round(float(mean_absolute_error(y_pru, base)), 2),
        mae_catalogo=round(float(mean_absolute_error(y_pru, cat_pru)), 2),
        segundos=round(segundos, 3),
    )

    if algoritmo == 'RF':
        resultado.importancias = _importancias(pipe)

    if guardar:
        marca = timezone.localtime().strftime('%Y%m%d_%H%M%S')
        ruta = os.path.join(directorio_modelos(),
                            f'modelo_{algoritmo.lower()}_{marca}.joblib')
        joblib.dump(pipe, ruta, compress=3)
        resultado.ruta = ruta
        resultado.tamano_kb = round(os.path.getsize(ruta) / 1024, 1)

    return resultado


def _importancias(pipe, limite=8):
    """Peso relativo de cada variable en el modelo de bosque aleatorio."""
    try:
        nombres = pipe.named_steps['preparacion'].get_feature_names_out()
        pesos = pipe.named_steps['estimador'].feature_importances_
    except Exception:
        return []
    pares = sorted(zip(nombres, pesos), key=lambda p: p[1], reverse=True)
    salida = []
    for nombre, peso in pares[:limite]:
        legible = (nombre.split('__', 1)[-1]
                   .replace('procedimiento_', 'Procedimiento: ')
                   .replace('odontologo_', 'Odontólogo: ')
                   .replace('dia_semana_', 'Día: ')
                   .replace('hora_inicio', 'Hora de inicio')
                   .replace('num_piezas', 'Número de piezas')
                   .replace('anestesia', 'Uso de anestesia')
                   .replace('complicacion', 'Complicación'))
        salida.append({'variable': legible, 'peso': round(float(peso) * 100, 1)})
    return salida


def registrar_version(resultado, activar=False, nombre=None):
    """Guarda la versión entrenada y, si procede, la pone en producción."""
    from .models import ModeloVersion

    version = ModeloVersion.objects.create(
        nombre=nombre or f'SmileeSync {resultado.algoritmo} '
                         f'{timezone.localdate():%d/%m/%Y}',
        algoritmo=resultado.algoritmo,
        mae=resultado.mae, rmse=resultado.rmse, r2=resultado.r2,
        mae_catalogo=resultado.mae_catalogo,
        fecha_entrenamiento=timezone.now(),
        ruta_archivo=resultado.ruta,
        activo=False,
    )
    if activar:
        activar_version(version)
    return version


def activar_version(version):
    """Pone una versión en producción y retira la anterior.

    Solo una versión está activa a la vez; las demás se conservan para poder
    comparar y, en caso necesario, volver atrás.
    """
    from .models import ModeloVersion
    from .servicio import limpiar_cache

    ModeloVersion.objects.filter(activo=True).exclude(pk=version.pk).update(activo=False)
    version.activo = True
    version.save(update_fields=['activo'])
    limpiar_cache()
    return version

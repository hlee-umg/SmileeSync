"""Evaluación del modelo contra lo que la clínica tardó en realidad.

El entrenamiento informa qué tan bien predice el modelo sobre el subconjunto
que se le reservó. Eso responde si el modelo aprendió, pero no si sirve: para
saberlo hay que contrastarlo con el método que la clínica usa hoy, que es
reservar el bloque que declara el catálogo.

Este módulo resuelve las dos lecturas que lo responden:

    retrospectiva  — sobre el subconjunto de prueba de cada versión entrenada,
                     el error del modelo frente al error del catálogo. Es la
                     medición con que se resuelve la hipótesis, porque ninguno
                     de esos registros intervino en el entrenamiento.
    prospectiva    — sobre las predicciones que el sistema emitió al agendar
                     citas que después se atendieron. Mide el desempeño en
                     operación real y se llena conforme la clínica usa el
                     sistema.
"""

from django.db.models import Avg, Count, F

from .entrenamiento import META_REDUCCION_PCT


def _media(valores):
    valores = list(valores)
    return round(sum(valores) / len(valores), 2) if valores else None


def resumen_version(version):
    """Lectura retrospectiva de una versión: modelo contra catálogo."""
    if version is None or version.mae is None or not version.mae_catalogo:
        return None
    reduccion = round(
        (version.mae_catalogo - version.mae) / version.mae_catalogo * 100, 1
    )
    return {
        "version": version,
        "mae_modelo": version.mae,
        "mae_catalogo": version.mae_catalogo,
        "reduccion_pct": reduccion,
        "meta_pct": META_REDUCCION_PCT,
        "cumple": reduccion >= META_REDUCCION_PCT,
    }


def contrastables():
    """Predicciones emitidas cuya cita ya fue atendida y medida."""
    from .models import Prediccion

    return Prediccion.objects.filter(
        cita__estado_cita="ATENDIDA",
        cita__duracion_real_min__isnull=False,
        cita__estado=True,
    ).select_related("cita", "cita__procedimiento", "modelo")


def desempeno_en_operacion():
    """Lectura prospectiva: qué tan cerca quedó cada predicción emitida.

    Mide tres cosas sobre las mismas citas: el error del modelo, el error de
    la duración del catálogo y la proporción de atenciones que cayeron dentro
    del bloque que el sistema había recomendado. La última es la que importa
    en la operación: una estimación que falla por dos minutos no desordena la
    agenda, pero una que se sale del bloque reservado sí.
    """
    filas = list(contrastables())
    if not filas:
        return None

    errores_modelo, errores_catalogo, dentro = [], [], 0
    for p in filas:
        real = p.cita.duracion_real_min
        errores_modelo.append(abs(p.duracion_estimada_min - real))
        errores_catalogo.append(abs(p.cita.procedimiento.duracion_promedio_min - real))
        if p.bloque_min_recomendado <= real <= p.bloque_max_recomendado:
            dentro += 1

    mae_modelo = _media(errores_modelo)
    mae_catalogo = _media(errores_catalogo)
    reduccion = (
        round((mae_catalogo - mae_modelo) / mae_catalogo * 100, 1)
        if mae_catalogo
        else 0.0
    )
    return {
        "predicciones": len(filas),
        "mae_modelo": mae_modelo,
        "mae_catalogo": mae_catalogo,
        "reduccion_pct": reduccion,
        "cumple": reduccion >= META_REDUCCION_PCT,
        "dentro_del_bloque": dentro,
        "dentro_pct": round(dentro / len(filas) * 100, 1),
    }


def desempeno_por_procedimiento(minimo=1):
    """Desglose de la lectura prospectiva por procedimiento."""
    por_proc = {}
    for p in contrastables():
        clave = p.cita.procedimiento.nombre
        real = p.cita.duracion_real_min
        d = por_proc.setdefault(
            clave,
            {
                "procedimiento": clave,
                "catalogo": p.cita.procedimiento.duracion_promedio_min,
                "errores_modelo": [],
                "errores_catalogo": [],
                "dentro": 0,
            },
        )
        d["errores_modelo"].append(abs(p.duracion_estimada_min - real))
        d["errores_catalogo"].append(abs(d["catalogo"] - real))
        if p.bloque_min_recomendado <= real <= p.bloque_max_recomendado:
            d["dentro"] += 1

    filas = []
    for d in por_proc.values():
        n = len(d["errores_modelo"])
        if n < minimo:
            continue
        filas.append(
            {
                "procedimiento": d["procedimiento"],
                "catalogo": d["catalogo"],
                "atenciones": n,
                "mae_modelo": _media(d["errores_modelo"]),
                "mae_catalogo": _media(d["errores_catalogo"]),
                "dentro_pct": round(d["dentro"] / n * 100, 1),
            }
        )
    return sorted(filas, key=lambda f: f["mae_modelo"], reverse=True)

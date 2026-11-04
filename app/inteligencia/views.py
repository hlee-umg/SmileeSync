"""Módulo de Inteligencia: versiones del modelo y su desempeño.

La pantalla no entrena: el entrenamiento se ejecuta con `manage.py entrenar`,
fuera del proceso web. Aquí se consulta qué versiones existen, cuál está en
producción y cuánto mejora cada una frente a estimar con la duración de
referencia del catálogo.
"""

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.decorators import escritura_requerida, modulo_requerido

from . import evaluacion
from .models import DatoEntrenamiento, ModeloVersion, Prediccion


def _desempeno_vigente():
    """Contraste entre la duración del catálogo y la real, por procedimiento.

    Es la medida que justifica el componente: indica cuánto se aleja la
    referencia del catálogo de lo que la clínica tarda en realidad.
    """
    from agenda.models import Cita
    from catalogo.models import Procedimiento

    filas = []
    for proc in Procedimiento.objects.filter(estado=True).order_by("nombre"):
        base = Cita.objects.filter(
            procedimiento=proc,
            estado_cita="ATENDIDA",
            duracion_real_min__isnull=False,
            estado=True,
        )
        n = base.count()
        if n < 3:
            continue
        real = base.aggregate(m=Avg("duracion_real_min"))["m"]
        filas.append(
            {
                "procedimiento": proc.nombre,
                "catalogo": proc.duracion_promedio_min,
                "real": round(real, 1),
                "error_catalogo": round(abs(real - proc.duracion_promedio_min), 1),
                "atenciones": n,
            }
        )
    return filas


@login_required
@modulo_requerido("inteligencia")
def panel(request):
    versiones = list(ModeloVersion.objects.filter(estado=True))
    activa = next((v for v in versiones if v.activo), None)

    from agenda.models import Cita

    atendidas = Cita.objects.filter(
        estado_cita="ATENDIDA", duracion_real_min__isnull=False, estado=True
    )
    total = atendidas.count()

    desempeno = _desempeno_vigente()
    error_catalogo = (
        round(sum(f["error_catalogo"] for f in desempeno) / len(desempeno), 2)
        if desempeno
        else None
    )

    # Serie para la gráfica comparativa de versiones.
    con_metrica = [v for v in reversed(versiones) if v.mae is not None]
    serie = {
        "etiquetas": [
            (
                f"{v.get_algoritmo_display()} · {v.fecha_entrenamiento:%d/%m}"
                if v.fecha_entrenamiento
                else v.nombre
            )
            for v in con_metrica
        ],
        "mae": [v.mae for v in con_metrica],
    }

    operacion = evaluacion.desempeno_en_operacion()
    contexto = {
        "versiones": versiones,
        "activa": activa,
        "validacion": evaluacion.resumen_version(activa),
        "operacion": operacion,
        "operacion_proc": evaluacion.desempeno_por_procedimiento() if operacion else [],
        "en_conjunto": DatoEntrenamiento.objects.count(),
        "registros": total,
        "minimo": 60,
        "suficientes": total >= 60,
        "desempeno": desempeno,
        "error_catalogo": error_catalogo,
        "predicciones": Prediccion.objects.count(),
        "serie_versiones": json.dumps(serie),
        "serie_desempeno": json.dumps(
            {
                "etiquetas": [f["procedimiento"] for f in desempeno],
                "catalogo": [f["catalogo"] for f in desempeno],
                "real": [f["real"] for f in desempeno],
            }
        ),
        "cobertura": (atendidas.filter(nota__isnull=False).count() if total else 0),
    }
    return render(request, "inteligencia/panel.html", contexto)


@login_required
@escritura_requerida("inteligencia")
def activar(request, pk):
    """Pone una versión del modelo en producción."""
    version = get_object_or_404(ModeloVersion, pk=pk, estado=True)
    if request.method == "POST":
        from .entrenamiento import activar_version

        activar_version(version)
        messages.success(
            request,
            f"La versión «{version.nombre}» quedó en producción. Las "
            f"estimaciones siguientes la utilizan.",
        )
    return redirect("inteligencia:panel")

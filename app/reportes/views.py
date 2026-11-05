"""Módulo de Reportes e Indicadores.

Presenta en una sola pantalla el desempeño operativo de la clínica y la
precisión de la estimación de duraciones. El último reporte es el que sustenta
el componente predictivo: contrasta la duración de referencia del catálogo con
la que la clínica tarda realmente.
"""

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from usuarios.decorators import modulo_requerido

from . import servicio

SEMANAS = [4, 8, 12, 26]


@login_required
@modulo_requerido("reportes")
def panel(request):
    semanas = request.GET.get("semanas", "8")
    semanas = int(semanas) if semanas.isdigit() and int(semanas) in SEMANAS else 8
    desde, hasta = servicio.rango(semanas)

    precision = servicio.precision_por_procedimiento(desde, hasta)
    contexto = {
        "semanas": semanas,
        "opciones": SEMANAS,
        "desde": desde,
        "hasta": hasta,
        "resumen": servicio.resumen(desde, hasta),
        "carga": servicio.carga_por_odontologo(desde, hasta),
        "frecuentes": servicio.procedimientos_frecuentes(desde, hasta),
        "precision": precision,
        "serie_semanal": json.dumps(servicio.atenciones_por_semana(desde, hasta)),
        "serie_horas": json.dumps(servicio.ocupacion_por_hora(desde, hasta)),
        "serie_precision": json.dumps(
            {
                "etiquetas": [f["nombre"] for f in precision],
                "catalogo": [f["catalogo"] for f in precision],
                "real": [f["real"] for f in precision],
            }
        ),
        "serie_carga": json.dumps(
            {
                "etiquetas": [
                    f["odontologo"] for f in servicio.carga_por_odontologo(desde, hasta)
                ],
                "horas": [
                    f["horas"] for f in servicio.carga_por_odontologo(desde, hasta)
                ],
                "utilizacion": [
                    f["utilizacion"]
                    for f in servicio.carga_por_odontologo(desde, hasta)
                ],
            }
        ),
        "generado": timezone.localtime(),
    }
    return render(request, "reportes/panel.html", contexto)

"""Contraste estadístico de la hipótesis de trabajo.

La sección 3.4.4 del documento fija la regla de decisión: se rechaza H0 cuando
la reducción del error absoluto medio frente al método de bloques fijos alcanza
al menos el 25 % y, además, la diferencia por pares resulta significativa en la
prueba de rangos con signo de Wilcoxon con α = 0.05.

La prueba se implementa aquí en lugar de incorporar SciPy por la misma razón
por la que se descartó XGBoost: una dependencia de cómputo científico pesa
decenas de megabytes en la instancia de producción y se emplearía una sola vez.
Con los tamaños de muestra de este proyecto —varios centenares de pares— la
aproximación normal del estadístico es válida, de modo que basta con corregir
por empates y por continuidad.
"""

from statistics import NormalDist

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from . import entrenamiento as E

REPETICIONES = 5
PLIEGUES = 10
ALFA = 0.05


def _rangos_promedio(valores):
    """Rangos de menor a mayor, promediando los empates."""
    orden = np.argsort(valores, kind="mergesort")
    rangos = np.empty(len(valores), dtype=float)
    i = 0
    while i < len(valores):
        j = i
        while j + 1 < len(valores) and valores[orden[j + 1]] == valores[orden[i]]:
            j += 1
        rangos[orden[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return rangos


def wilcoxon(diferencias):
    """Prueba de rangos con signo para una muestra pareada.

    Devuelve el número de pares no nulos, el estadístico W+, el valor z y el
    valor p bilateral. Los pares con diferencia cero se descartan, conforme al
    procedimiento clásico.
    """
    d = np.asarray([x for x in diferencias if x != 0], dtype=float)
    n = len(d)
    if n < 10:
        raise ValueError("Se requieren al menos diez pares no nulos.")
    rangos = _rangos_promedio(np.abs(d))
    w_mas = float(rangos[d > 0].sum())
    media = n * (n + 1) / 4
    varianza = n * (n + 1) * (2 * n + 1) / 24

    # Corrección por empates: cada grupo de |d| repetidos resta varianza.
    absolutos = np.abs(d)
    _, cuentas = np.unique(absolutos, return_counts=True)
    varianza -= sum(t**3 - t for t in cuentas if t > 1) / 48

    desviacion = varianza**0.5
    continuidad = 0.5 if w_mas > media else -0.5
    z = (w_mas - media - continuidad) / desviacion
    p = 2 * (1 - NormalDist().cdf(abs(z)))
    return {
        "pares": n,
        "w_mas": round(w_mas, 1),
        "z": round(z, 4),
        "p": p,
        "mediana_diferencia": round(float(np.median(d)), 2),
    }


def errores_pareados(repeticiones=REPETICIONES, pliegues=PLIEGUES):
    """Error absoluto del modelo y del catálogo sobre cada atención.

    Las predicciones se obtienen por validación cruzada repetida: en cada
    repetición el modelo se entrena sin el pliegue que después predice, de modo
    que ninguna atención se estima con un modelo que la haya visto. Las
    predicciones de las repeticiones se promedian por registro antes del
    contraste, para que cada atención aporte un único par.
    """
    registros = E.reunir_datos()
    if len(registros) < E.MINIMO_REGISTROS:
        return None
    df = pd.DataFrame(registros)
    y = df["duracion_real_min"].to_numpy(dtype=float)
    catalogo = df["duracion_catalogo"].to_numpy(dtype=float)
    X = df.drop(columns=["duracion_real_min", "duracion_catalogo"])

    acumulado = np.zeros(len(df), dtype=float)
    for r in range(repeticiones):
        kf = KFold(n_splits=pliegues, shuffle=True, random_state=42 + r)
        for ent, pru in kf.split(X):
            modelo = E._construir("RF")
            modelo.fit(X.iloc[ent], y[ent])
            acumulado[pru] += modelo.predict(X.iloc[pru])
    predicho = acumulado / repeticiones
    return {
        "n": len(df),
        "error_modelo": np.abs(y - predicho),
        "error_catalogo": np.abs(y - catalogo),
    }


def contrastar():
    """Ejecuta el contraste completo y devuelve el veredicto sobre H0."""
    datos = errores_pareados()
    if datos is None:
        return None
    em, ec = datos["error_modelo"], datos["error_catalogo"]
    mae_modelo, mae_catalogo = float(em.mean()), float(ec.mean())
    reduccion = (mae_catalogo - mae_modelo) / mae_catalogo * 100
    prueba = wilcoxon(ec - em)
    cumple_meta = reduccion >= E.META_REDUCCION_PCT
    significativa = prueba["p"] < ALFA
    return {
        "n": datos["n"],
        "mae_modelo": round(mae_modelo, 2),
        "mae_catalogo": round(mae_catalogo, 2),
        "reduccion_pct": round(reduccion, 1),
        "meta_pct": E.META_REDUCCION_PCT,
        "cumple_meta": cumple_meta,
        "alfa": ALFA,
        "significativa": significativa,
        "rechaza_h0": cumple_meta and significativa,
        **prueba,
    }

"""Unitarias: contraste de la hipótesis con la prueba de Wilcoxon.

La prueba se implementa sin SciPy; aquí se verifica contra ``scipy.stats``
(disponible en el entorno de pruebas como dependencia de scikit-learn).
"""

from io import StringIO

import numpy as np
import pytest
from django.core.management import call_command

from inteligencia import contraste
from inteligencia import entrenamiento as E

pytestmark = pytest.mark.unit


def test_rangos_promedia_los_empates():
    rangos = contraste._rangos_promedio(np.array([3.0, 1.0, 3.0, 2.0]))
    assert rangos.tolist() == [3.5, 1.0, 3.5, 2.0]


def test_wilcoxon_coincide_con_scipy():
    stats = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(7)
    diferencias = np.round(rng.normal(0.8, 2.0, 120), 1)
    propio = contraste.wilcoxon(diferencias)
    referencia = stats.wilcoxon(
        diferencias, zero_method="wilcox", correction=True, method="approx"
    )
    assert propio["pares"] == int(np.count_nonzero(diferencias))
    assert propio["p"] == pytest.approx(referencia.pvalue, rel=1e-6)


def test_wilcoxon_descarta_ceros_y_exige_diez_pares():
    with pytest.raises(ValueError):
        contraste.wilcoxon([0, 0, 1, -1, 2, 3, 0, 4, 5, 6, 7])


def _datos(error_catalogo, error_modelo):
    return {
        "n": len(error_catalogo),
        "error_catalogo": np.array(error_catalogo, dtype=float),
        "error_modelo": np.array(error_modelo, dtype=float),
    }


def test_contrastar_rechaza_h0_cuando_cumple_las_dos_condiciones(monkeypatch):
    catalogo = [10.0 + i for i in range(30)]
    modelo = [2.0 + (i % 3) for i in range(30)]
    monkeypatch.setattr(contraste, "errores_pareados", lambda: _datos(catalogo, modelo))
    r = contraste.contrastar()
    assert r["cumple_meta"] and r["significativa"] and r["rechaza_h0"]
    assert r["reduccion_pct"] >= E.META_REDUCCION_PCT


def test_contrastar_no_rechaza_si_la_reduccion_no_alcanza_la_meta(monkeypatch):
    catalogo = [10.0 + (i % 5) for i in range(40)]
    modelo = [c - 0.5 for c in catalogo]
    monkeypatch.setattr(contraste, "errores_pareados", lambda: _datos(catalogo, modelo))
    r = contraste.contrastar()
    assert not r["cumple_meta"]
    assert not r["rechaza_h0"]


def test_contrastar_sin_registros_devuelve_none(monkeypatch):
    monkeypatch.setattr(E, "reunir_datos", lambda: [])
    assert contraste.errores_pareados() is None
    assert contraste.contrastar() is None


class _Promedio:
    def fit(self, X, y):
        self.media = float(np.mean(y))
        return self

    def predict(self, X):
        return np.full(len(X), self.media)


def test_errores_pareados_usa_validacion_cruzada(monkeypatch):
    registros = [
        {"x": float(i), "duracion_real_min": 20.0 + i % 7, "duracion_catalogo": 25.0}
        for i in range(40)
    ]
    monkeypatch.setattr(E, "MINIMO_REGISTROS", 10)
    monkeypatch.setattr(E, "reunir_datos", lambda: registros)
    monkeypatch.setattr(E, "_construir", lambda codigo: _Promedio())
    datos = contraste.errores_pareados(repeticiones=2, pliegues=5)
    assert datos["n"] == 40
    assert len(datos["error_modelo"]) == 40
    assert np.all(datos["error_catalogo"] >= 0)


def test_comando_contrastar_informa_el_veredicto(monkeypatch):
    resultado = {
        "n": 446,
        "mae_catalogo": 7.02,
        "mae_modelo": 3.97,
        "reduccion_pct": 43.5,
        "meta_pct": 25,
        "pares": 440,
        "w_mas": 71170.0,
        "z": 7.8312,
        "p": 4.88e-15,
        "mediana_diferencia": 1.13,
        "rechaza_h0": True,
    }
    monkeypatch.setattr(
        "inteligencia.management.commands.contrastar.contrastar", lambda: resultado
    )
    salida = StringIO()
    call_command("contrastar", stdout=salida)
    assert "Se rechaza H0" in salida.getvalue()


def test_comando_contrastar_sin_datos(monkeypatch):
    monkeypatch.setattr(
        "inteligencia.management.commands.contrastar.contrastar", lambda: None
    )
    salida = StringIO()
    call_command("contrastar", stdout=salida)
    assert "No hay registros suficientes" in salida.getvalue()

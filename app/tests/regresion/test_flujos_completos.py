"""Regresión: flujos completos del sistema.

Los scripts ``prueba_*.py`` recorren de punta a punta los ocho módulos con
peticiones HTTP reales (336 verificaciones en total). Antes se ejecutaban a
mano sobre la base de datos de desarrollo, por lo que su resultado dependía de
lo que hubiera en ella. Aquí cada script corre sobre una base de datos de
prueba nueva, sembrada con ``manage.py seed``, y la prueba falla si alguna
verificación falla o si el script se interrumpe.
"""

import contextlib
import io
import runpy
from pathlib import Path

import pytest
from django.core.management import call_command

SCRIPTS = Path(__file__).parent
FLUJOS = [
    "horarios",
    "permisos",
    "calendario",
    "recomendacion",
    "flujos",
    "capacidad",
    "clinico",
    "modelo",
]


@pytest.fixture
def base_sembrada(db, settings, tmp_path, monkeypatch):
    settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
    # Los modelos que entrena `prueba_modelo` se escriben en una carpeta
    # temporal y no en app/modelos/.
    monkeypatch.setattr(
        "inteligencia.entrenamiento.directorio_modelos", lambda: str(tmp_path)
    )
    # Las cuentas de demostración toman su contraseña de esta variable.
    monkeypatch.setenv("SEED_PASSWORD", "Clave-demo-regresion-1")
    call_command("seed", stdout=io.StringIO())


@pytest.mark.regression
@pytest.mark.parametrize("flujo", FLUJOS)
def test_flujo_sin_verificaciones_fallidas(base_sembrada, flujo):
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        resultado = runpy.run_path(str(SCRIPTS / f"prueba_{flujo}.py"))

    fallidas = [
        linea.strip()
        for linea in salida.getvalue().splitlines()
        if linea.strip().startswith("FALLA")
    ]
    assert resultado["ok"] > 0, "el script no ejecutó ninguna verificación"
    assert resultado["fallo"] == 0, "\n".join(fallidas)

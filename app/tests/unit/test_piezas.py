"""Unitarias: nomenclatura FDI de piezas dentales (clinico/piezas.py)."""
import pytest

from clinico import piezas

pytestmark = pytest.mark.unit


def test_denticion_permanente_tiene_32_piezas():
    assert len(piezas.PIEZAS) == 32
    assert len(set(piezas.PIEZAS)) == 32


@pytest.mark.parametrize('pieza', [11, 18, 21, 28, 31, 38, 41, 48, '36'])
def test_piezas_validas(pieza):
    assert piezas.es_valida(pieza)


@pytest.mark.parametrize('pieza', [10, 19, 51, 85, 0, None, 'abc'])
def test_piezas_invalidas_o_temporales(pieza):
    assert not piezas.es_valida(pieza)


@pytest.mark.parametrize('pieza, nombre', [
    (11, 'Incisivo central superior derecho'),
    (23, 'Canino superior izquierdo'),
    (36, 'Primer molar inferior izquierdo'),
    (48, 'Tercer molar inferior derecho'),
])
def test_nombre_legible(pieza, nombre):
    assert piezas.nombre(pieza) == nombre


def test_nombre_de_pieza_invalida_devuelve_el_valor():
    assert piezas.nombre(99) == '99'


def test_filas_arcada_en_orden_de_dibujo():
    filas = piezas.filas_arcada()
    assert [f['cuadrante'] for f in filas] == [1, 2, 4, 3]
    assert all(len(f['piezas']) == 8 for f in filas)

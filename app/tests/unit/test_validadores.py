"""Unitarias: validadores compartidos (config/validadores.py)."""

import pytest
from django.core.exceptions import ValidationError

from config.validadores import (
    MENSAJE_EMAIL,
    validar_codigo,
    validar_email_real,
    validar_nombre,
    validar_telefono,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("nombre", ["María José", "López-García", "O'Connor", "Ñuñez"])
def test_nombre_acepta_tildes_compuestos_y_guiones(nombre):
    assert validar_nombre(f"  {nombre}  ") == nombre


@pytest.mark.parametrize(
    "nombre", ["Juan2", "Ana@", "-Luis", "José--María", "Ana  María"]
)
def test_nombre_rechaza_numeros_y_caracteres_especiales(nombre):
    with pytest.raises(ValidationError, match="solo puede contener letras"):
        validar_nombre(nombre)


@pytest.mark.parametrize("vacio", ["", "   ", None])
def test_nombre_vacio_es_obligatorio(vacio):
    with pytest.raises(ValidationError, match="obligatorio"):
        validar_nombre(vacio, "apellido")


def test_email_se_normaliza_a_minusculas():
    assert validar_email_real("  Ana.Lopez@Correo.GT ") == "ana.lopez@correo.gt"


@pytest.mark.parametrize("correo", ["ana", "ana@", "@correo.gt", "ana@correo"])
def test_email_con_formato_invalido_usa_mensaje_unico(correo):
    with pytest.raises(ValidationError) as error:
        validar_email_real(correo)
    assert error.value.messages == [MENSAJE_EMAIL]


def test_email_opcional_admite_vacio():
    assert validar_email_real("", obligatorio=False) == ""


def test_email_obligatorio_rechaza_vacio():
    with pytest.raises(ValidationError, match="obligatorio"):
        validar_email_real("")


@pytest.mark.parametrize(
    "entrada, esperado",
    [("pac-0001", "PAC-0001"), (" proc-14 ", "PROC-14"), ("A1", "A1")],
)
def test_codigo_valido_se_normaliza_a_mayusculas(entrada, esperado):
    assert validar_codigo(entrada) == esperado


@pytest.mark.parametrize("codigo", ["PAC_01", "-PAC", "PAC-", "P", "PAC 01"])
def test_codigo_invalido_se_rechaza(codigo):
    with pytest.raises(ValidationError, match="letras, números y guiones"):
        validar_codigo(codigo)


def test_codigo_vacio_es_obligatorio():
    with pytest.raises(ValidationError, match="obligatorio"):
        validar_codigo("")


@pytest.mark.parametrize("telefono", ["5555-1234", "+502 5555 1234", "(502) 2222-3333"])
def test_telefono_valido(telefono):
    assert validar_telefono(telefono) == telefono


@pytest.mark.parametrize("telefono", ["12345", "cinco55551234", "5555/1234"])
def test_telefono_invalido(telefono):
    with pytest.raises(ValidationError):
        validar_telefono(telefono)


def test_telefono_es_opcional():
    assert validar_telefono("  ") == ""

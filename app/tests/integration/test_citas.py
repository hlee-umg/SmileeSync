"""Integración: programación y cancelación de citas."""

from datetime import time, timedelta

import pytest
from django.urls import reverse

from agenda.models import Cita, HistorialCita
from tests.conftest import LUNES

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture
def datos_cita(paciente, odontologo, procedimiento, unidades):
    def construir(**cambios):
        datos = {
            "paciente": paciente.pk,
            "odontologo": odontologo.pk,
            "procedimiento": procedimiento.pk,
            "fecha": LUNES.isoformat(),
            "hora_inicio_programada": "10:00",
            "duracion_asignada_min": 30,
            "num_piezas": 1,
            "observaciones": "",
        }
        datos.update(cambios)
        return datos

    return construir


def test_programar_cita_asigna_unidad_y_hora_fin(cliente_recepcion, datos_cita):
    r = cliente_recepcion.post(reverse("agenda:crear"), datos_cita())
    assert r.status_code == 302
    cita = Cita.objects.get()
    assert cita.hora_fin_programada == time(10, 30)
    assert cita.unidad.codigo == "SIL-01"


@pytest.mark.parametrize(
    "cambios, mensaje",
    [
        ({"hora_inicio_programada": "11:45"}, "fuera del horario"),
        ({"fecha": (LUNES + timedelta(days=1)).isoformat()}, "no tiene horario"),
        ({"fecha": "2020-01-06"}, "fecha pasada"),
    ],
)
def test_programar_fuera_de_disponibilidad_se_rechaza(
    cliente_recepcion, datos_cita, cambios, mensaje
):
    r = cliente_recepcion.post(reverse("agenda:crear"), datos_cita(**cambios))
    assert r.status_code == 200
    assert mensaje in r.content.decode()
    assert not Cita.objects.exists()


def test_no_se_traslapan_citas_del_mismo_odontologo(
    cliente_recepcion, datos_cita, cita
):
    r = cliente_recepcion.post(
        reverse("agenda:crear"), datos_cita(hora_inicio_programada="09:15")
    )
    assert r.status_code == 200
    assert Cita.objects.count() == 1


def test_cancelar_conserva_el_registro_y_audita(cliente_recepcion, cita):
    r = cliente_recepcion.post(
        reverse("agenda:cancelar", args=[cita.pk]),
        {"motivo": "El paciente avisó que no asistirá"},
    )
    assert r.status_code == 302
    cita.refresh_from_db()
    assert cita.estado_cita == "CANCELADA"
    assert cita.estado is True
    assert "no asistirá" in cita.observaciones
    assert (
        HistorialCita.objects.get(cita_ref=cita.pk).estado_cita_anterior == "PROGRAMADA"
    )


def test_cancelar_redirige_a_una_pagina_interna(cliente_recepcion, cita):
    destino = reverse("agenda:detalle", args=[cita.pk])
    r = cliente_recepcion.post(
        reverse("agenda:cancelar", args=[cita.pk]), {"siguiente": destino}
    )
    assert r.url == destino


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason="BUG-01: Open Redirect en agenda.views.cancelar "
    "(SonarCloud, Blocker). Pendiente de corrección.",
)
def test_cancelar_no_redirige_a_un_sitio_externo(cliente_recepcion, cita):
    r = cliente_recepcion.post(
        reverse("agenda:cancelar", args=[cita.pk]),
        {"siguiente": "https://sitio-malicioso.example/robo"},
    )
    assert not r.url.startswith("http")

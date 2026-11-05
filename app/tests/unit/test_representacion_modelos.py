"""Unitarias: representación legible de los registros (``__str__``).

Es lo que se muestra en el sitio de administración y en los mensajes de
error; un registro sin ``__str__`` aparece como "Objeto (12)".
"""

from datetime import date, time

import pytest

from agenda.models import HistorialCita, HorarioDisponibilidad
from clinico.models import HistorialPlan
from inteligencia.models import DatoEntrenamiento, Prediccion
from pacientes.models import HistorialPaciente
from reportes.models import IndicadorDesempeno
from usuarios.models import HistorialUsuario

pytestmark = pytest.mark.unit


def test_horario_muestra_odontologo_dia_y_franja(odontologo):
    horario = HorarioDisponibilidad.objects.get(odontologo=odontologo)
    assert str(horario) == "Carlos Pérez — Lunes 08:00 a 12:00"


@pytest.mark.parametrize(
    "registro, esperado",
    [
        (
            HistorialCita(cita_ref=7, accion="CANCELACION", realizado_por="ana"),
            "Cita 7: CANCELACION por ana",
        ),
        (
            HistorialPlan(codigo="PT-0003", accion="PAGO", realizado_por="ana"),
            "Plan PT-0003: PAGO por ana",
        ),
        (
            HistorialPaciente(
                codigo="PAC-0001", accion="CREACION", realizado_por="ana"
            ),
            "PAC-0001: CREACION por ana",
        ),
        (
            HistorialUsuario(username="luis", accion="ACTIVACION", realizado_por="ana"),
            "luis: ACTIVACION por ana",
        ),
        (
            DatoEntrenamiento(cita_id=15),
            "Dato de entrenamiento de la cita 15",
        ),
        (
            Prediccion(cita_id=15, duracion_estimada_min=45),
            "Predicción de 45 min para la cita 15",
        ),
        (
            IndicadorDesempeno(fecha=date(2026, 11, 3)),
            "Indicadores del 03/11/2026",
        ),
    ],
)
def test_registros_de_auditoria_e_indicadores(registro, esperado):
    assert str(registro) == esperado


def test_horario_con_minutos(odontologo):
    horario = HorarioDisponibilidad(
        odontologo=odontologo,
        dia_semana="VIE",
        hora_inicio=time(14, 30),
        hora_fin=time(18, 15),
    )
    assert str(horario).endswith("Viernes 14:30 a 18:15")

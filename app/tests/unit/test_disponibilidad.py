"""Unitarias: disponibilidad de odontólogos y unidades (agenda/disponibilidad.py)."""
from datetime import time, timedelta

import pytest

from agenda import disponibilidad as disp
from agenda.models import AusenciaOdontologo, Cita
from tests.conftest import LUNES

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('a, b, traslapan', [
    ((9, 10), (9, 10), True),     # idénticos
    ((9, 10), (9.5, 11), True),   # parcial
    ((9, 12), (10, 11), True),    # uno contiene al otro
    ((9, 10), (10, 11), False),   # contiguos: uno termina cuando empieza el otro
    ((9, 10), (11, 12), False),   # separados
])
def test_hay_traslape(a, b, traslapan):
    assert disp.hay_traslape(a[0], a[1], b[0], b[1]) is traslapan


@pytest.mark.parametrize('quitar, esperado', [
    ((0, 60), [(60, 240)]),               # recorta el inicio
    ((180, 300), [(0, 180)]),             # recorta el final
    ((60, 120), [(0, 60), (120, 240)]),   # parte en dos
    ((0, 240), []),                       # elimina todo
    ((300, 400), [(0, 240)]),             # no se tocan
])
def test_restar_intervalos(quitar, esperado):
    assert disp._restar([(0, 240)], quitar) == esperado


def test_a_hora_acota_al_dia():
    assert disp._a_hora(-10) == time(0, 0)
    assert disp._a_hora(24 * 60 + 5) == time(23, 59)
    assert disp._a_hora(9 * 60 + 30) == time(9, 30)


@pytest.mark.django_db
def test_franja_efectiva_es_el_horario_semanal(odontologo):
    assert disp.franjas_efectivas(odontologo, LUNES) == [(time(8, 0), time(12, 0))]


@pytest.mark.django_db
def test_sin_horario_ese_dia_no_hay_franjas(odontologo):
    martes = LUNES + timedelta(days=1)
    assert disp.franjas_efectivas(odontologo, martes) == []


@pytest.mark.django_db
def test_ausencia_parcial_parte_la_franja(odontologo):
    AusenciaOdontologo.objects.create(odontologo=odontologo, fecha=LUNES, todo_el_dia=False,
                                      hora_inicio=time(9, 0), hora_fin=time(10, 0))
    assert disp.franjas_efectivas(odontologo, LUNES) == [
        (time(8, 0), time(9, 0)), (time(10, 0), time(12, 0))]


@pytest.mark.django_db
def test_ausencia_de_todo_el_dia_elimina_la_disponibilidad(odontologo):
    AusenciaOdontologo.objects.create(odontologo=odontologo, fecha=LUNES,
                                      hora_inicio=time(0, 0), hora_fin=time(23, 59))
    assert disp.franjas_efectivas(odontologo, LUNES) == []
    assert not disp.cabe_en_franja(odontologo, LUNES, time(9, 0), time(9, 30))


@pytest.mark.django_db
def test_ausencia_inactiva_no_cuenta(odontologo):
    AusenciaOdontologo.objects.create(odontologo=odontologo, fecha=LUNES, estado=False,
                                      hora_inicio=time(0, 0), hora_fin=time(23, 59))
    assert disp.franjas_efectivas(odontologo, LUNES) != []


@pytest.mark.django_db
@pytest.mark.parametrize('inicio, fin, cabe', [
    (time(8, 0), time(12, 0), True),
    (time(11, 30), time(12, 0), True),
    (time(11, 30), time(12, 30), False),   # se sale de la franja
    (time(7, 30), time(8, 30), False),     # empieza antes
])
def test_cabe_en_franja(odontologo, inicio, fin, cabe):
    assert disp.cabe_en_franja(odontologo, LUNES, inicio, fin) is cabe


@pytest.mark.django_db
def test_unidad_ocupada_no_esta_libre(cita, unidades):
    libres = disp.unidades_libres(LUNES, time(9, 15), time(9, 45))
    assert libres == [unidades[1]]
    assert disp.asignar_unidad(LUNES, time(9, 15), time(9, 45)) == unidades[1]


@pytest.mark.django_db
def test_cita_cancelada_libera_la_unidad(cita, unidades):
    cita.estado_cita = 'CANCELADA'
    cita.save()
    assert disp.unidades_libres(LUNES, time(9, 0), time(9, 30)) == unidades


@pytest.mark.django_db
def test_excluir_la_propia_cita_al_reprogramar(cita, unidades):
    libres = disp.unidades_libres(LUNES, time(9, 0), time(9, 30), excluir_cita=cita.pk)
    assert libres == unidades


@pytest.mark.django_db
def test_sin_unidades_libres_no_se_asigna(cita, unidades, paciente, odontologo, procedimiento):
    Cita.objects.create(paciente=paciente, odontologo=odontologo, procedimiento=procedimiento,
                        unidad=unidades[1], fecha=LUNES, hora_inicio_programada=time(9, 0),
                        hora_fin_programada=time(9, 30), duracion_asignada_min=30)
    assert disp.asignar_unidad(LUNES, time(9, 0), time(9, 30)) is None


@pytest.mark.django_db
def test_capacidad_limitada_por_unidades(odontologo, unidades):
    # Un odontólogo de 8:00 a 12:00 y dos sillones: la capacidad es la del odontólogo.
    assert disp.capacidad_minutos([odontologo], [LUNES]) == 240


@pytest.mark.django_db
def test_sin_unidades_activas_la_capacidad_es_cero(odontologo):
    assert disp.capacidad_minutos([odontologo], [LUNES]) == 0

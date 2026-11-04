"""Integración: control de acceso por rol (RBAC) en las vistas.

La restricción no depende de ocultar botones: se verifica que el acceso directo
a la dirección también quede denegado.
"""
import pytest
from django.urls import reverse

from pacientes.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.mark.parametrize('ruta', ['usuarios:lista', 'usuarios:crear', 'usuarios:historial'])
def test_recepcion_no_entra_al_modulo_de_usuarios(cliente_recepcion, ruta):
    assert cliente_recepcion.get(reverse(ruta)).status_code == 403


def test_recepcion_no_entra_al_catalogo(cliente_recepcion):
    r = cliente_recepcion.get(reverse('catalogo:lista', args=['unidades']))
    assert r.status_code == 403


def test_consulta_ve_pacientes_pero_no_los_crea(cliente_consulta, paciente):
    assert cliente_consulta.get(reverse('pacientes:lista')).status_code == 200
    assert cliente_consulta.get(reverse('pacientes:crear')).status_code == 403


def test_consulta_no_puede_desactivar_por_acceso_directo(cliente_consulta, paciente):
    r = cliente_consulta.post(reverse('pacientes:estado', args=[paciente.pk]))
    assert r.status_code == 403
    paciente.refresh_from_db()
    assert paciente.estado is True


def test_consulta_no_cancela_citas(cliente_consulta, cita):
    r = cliente_consulta.post(reverse('agenda:cancelar', args=[cita.pk]))
    assert r.status_code == 403
    cita.refresh_from_db()
    assert cita.estado_cita == 'PROGRAMADA'


def test_escritura_sin_sesion_redirige_al_login(client, paciente):
    r = client.post(reverse('pacientes:estado', args=[paciente.pk]))
    assert r.status_code == 302
    assert Paciente.objects.get().estado is True


def test_usuario_sin_rol_no_accede(client, db):
    from tests.conftest import crear_usuario
    client.force_login(crear_usuario('sinrol@prueba.gt'))
    assert client.get(reverse('pacientes:lista')).status_code == 403

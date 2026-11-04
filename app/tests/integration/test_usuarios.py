"""Integración: administración de usuarios con auditoría."""
import pytest
from django.urls import reverse

from tests.conftest import CLAVE, crear_usuario
from usuarios.models import HistorialUsuario, Usuario

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def datos_usuario(rol, **cambios):
    datos = {'email': 'Nuevo@Prueba.gt', 'first_name': 'Luis', 'last_name': 'Morales',
             'telefono': '5555-9999', 'rol': rol.pk, 'pregunta_secreta': 'CIUDAD',
             'respuesta_secreta': 'Antigua', 'password1': CLAVE, 'password2': CLAVE}
    datos.update(cambios)
    return datos


def test_crear_usuario_usa_el_correo_como_usuario(cliente_admin, rol_recepcion):
    r = cliente_admin.post(reverse('usuarios:crear'), datos_usuario(rol_recepcion))
    assert r.url == reverse('usuarios:lista')
    nuevo = Usuario.objects.get(email='nuevo@prueba.gt')
    assert nuevo.username == 'nuevo@prueba.gt'
    assert nuevo.check_password(CLAVE)
    assert nuevo.check_respuesta_secreta('antigua')
    assert HistorialUsuario.objects.get(usuario_ref=nuevo.pk).accion == 'CREACION'


@pytest.mark.parametrize('cambios, mensaje', [
    ({'password2': 'otra-clave'}, 'no coinciden'),
    ({'email': 'admin@prueba.gt'}, 'Ya existe un usuario'),
    ({'first_name': 'Luis1'}, 'solo puede contener letras'),
])
def test_crear_usuario_invalido(cliente_admin, rol_recepcion, cambios, mensaje):
    r = cliente_admin.post(reverse('usuarios:crear'), datos_usuario(rol_recepcion, **cambios))
    assert r.status_code == 200
    assert mensaje in r.content.decode()


def editar_recepcionista(cliente, usuario, rol):
    return cliente.post(reverse('usuarios:editar', args=[usuario.pk]), {
        'email': usuario.email, 'first_name': 'Rosa', 'last_name': 'Girón',
        'telefono': '', 'rol': rol.pk, 'pregunta_secreta': ''})


def test_editar_usuario_actualiza_y_audita(cliente_admin, recepcionista, rol_consulta):
    r = editar_recepcionista(cliente_admin, recepcionista, rol_consulta)
    assert r.status_code == 302
    recepcionista.refresh_from_db()
    assert recepcionista.rol == rol_consulta
    assert HistorialUsuario.objects.filter(accion='ACTUALIZACION').count() == 1


@pytest.mark.regression
@pytest.mark.xfail(strict=True, reason='BUG-02: la auditoría de edición guarda los datos '
                                       'nuevos en lugar del estado previo. Pendiente.')
def test_auditoria_de_edicion_guarda_el_estado_previo(cliente_admin, recepcionista,
                                                      rol_consulta):
    editar_recepcionista(cliente_admin, recepcionista, rol_consulta)
    registro = HistorialUsuario.objects.get(accion='ACTUALIZACION')
    assert registro.rol == 'Recepcionista'


def test_desactivar_usuario_impide_iniciar_sesion(cliente_admin, recepcionista):
    cliente_admin.post(reverse('usuarios:cambiar_estado', args=[recepcionista.pk]))
    recepcionista.refresh_from_db()
    assert recepcionista.estado is False and recepcionista.is_active is False


def test_no_puede_desactivar_su_propia_cuenta(cliente_admin, admin):
    cliente_admin.post(reverse('usuarios:cambiar_estado', args=[admin.pk]))
    admin.refresh_from_db()
    assert admin.estado is True


def test_lista_busqueda_e_historial(cliente_admin, recepcionista):
    r = cliente_admin.get(reverse('usuarios:lista'), {'q': 'recepcion'})
    assert recepcionista in r.context['usuarios']
    crear_usuario('otro@prueba.gt')
    assert cliente_admin.get(reverse('usuarios:historial')).status_code == 200
    assert cliente_admin.get(reverse('usuarios:editar', args=[recepcionista.pk])).status_code == 200
    assert cliente_admin.get(reverse('usuarios:crear')).status_code == 200

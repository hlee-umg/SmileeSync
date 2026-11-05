"""Unitarias: permisos por rol (RBAC) y autenticación por correo."""

import pytest
from django.contrib.auth import authenticate

from tests.conftest import CLAVE, crear_rol, crear_usuario
from usuarios.models import HistorialUsuario

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_administrador_puede_todo(admin):
    assert admin.es_admin
    assert admin.puede("finanzas")
    assert admin.puede_escribir("clinico")
    assert not admin.es_solo_consulta


def test_superusuario_sin_rol_es_administrador():
    root = crear_usuario("root@prueba.gt", is_superuser=True)
    assert root.es_admin and root.puede("reportes")


def test_usuario_sin_rol_no_accede_a_ningun_modulo():
    usuario = crear_usuario("sinrol@prueba.gt")
    assert not usuario.puede("pacientes")
    assert not usuario.puede_escribir("pacientes")


def test_rol_accede_solo_a_sus_modulos(recepcionista):
    assert recepcionista.puede("agenda")
    assert not recepcionista.puede("usuarios")
    assert recepcionista.puede_escribir("agenda")
    assert not recepcionista.puede_escribir("usuarios")


def test_rol_de_consulta_ve_pero_no_escribe(consulta):
    assert consulta.es_solo_consulta
    assert consulta.puede("pacientes")
    assert not consulta.puede_escribir("pacientes")


def test_expediente_lo_escribe_quien_tiene_escritura_clinica(rol_odontologo):
    odontologo = crear_usuario("odo@prueba.gt", rol_odontologo)
    assert odontologo.puede_escribir("clinico")
    assert not odontologo.puede_escribir("agenda")


def test_acceso_al_expediente_sin_escritura_clinica_es_de_lectura():
    rol = crear_rol("Recepción clínica", ["clinico"])
    usuario = crear_usuario("rc@prueba.gt", rol)
    assert usuario.puede("clinico")
    assert not usuario.puede_escribir("clinico")


def test_respuesta_secreta_se_guarda_cifrada_e_ignora_mayusculas(admin):
    admin.set_respuesta_secreta("  Firulais ")
    assert "firulais" not in admin.respuesta_secreta.lower()
    assert admin.check_respuesta_secreta("FIRULAIS")
    assert not admin.check_respuesta_secreta("otra")


def test_sin_respuesta_secreta_no_valida(admin):
    assert not admin.check_respuesta_secreta("lo que sea")


def test_historial_copia_el_estado_previo(admin):
    HistorialUsuario.registrar(admin, "DESACTIVACION", "auditor")
    registro = HistorialUsuario.objects.get()
    assert registro.usuario_ref == admin.pk
    assert registro.rol == "Administrador"
    assert registro.estado_anterior is True
    assert registro.realizado_por == "auditor"


def test_login_por_correo_sin_importar_mayusculas(admin):
    assert authenticate(username="ADMIN@prueba.gt", password=CLAVE) == admin


def test_login_con_clave_incorrecta_falla(admin):
    assert authenticate(username="admin@prueba.gt", password="incorrecta") is None


def test_login_de_correo_inexistente_falla(db):
    assert authenticate(username="nadie@prueba.gt", password=CLAVE) is None


def test_login_sin_datos_falla(db):
    assert authenticate(username="", password="") is None


def test_usuario_inactivo_no_inicia_sesion(admin):
    admin.is_active = False
    admin.save()
    assert authenticate(username="admin@prueba.gt", password=CLAVE) is None

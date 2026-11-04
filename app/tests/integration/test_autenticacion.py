"""Integración: inicio de sesión, cierre de sesión y recuperación de contraseña."""

import pytest
from django.urls import reverse

from tests.conftest import CLAVE

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_pagina_protegida_redirige_al_login(client):
    respuesta = client.get(reverse("pacientes:lista"))
    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse("login"))


def test_login_por_correo_entra_a_la_agenda(client, admin):
    respuesta = client.post(
        reverse("login"), {"username": "admin@prueba.gt", "password": CLAVE}
    )
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("agenda:principal")


def test_login_con_clave_incorrecta_muestra_el_formulario(client, admin):
    respuesta = client.post(
        reverse("login"), {"username": "admin@prueba.gt", "password": "incorrecta"}
    )
    assert respuesta.status_code == 200
    assert "_auth_user_id" not in client.session


def test_logout_cierra_la_sesion(cliente_admin):
    cliente_admin.post(reverse("logout"))
    respuesta = cliente_admin.get(reverse("pacientes:lista"))
    assert respuesta.status_code == 302


def test_paginas_dinamicas_no_se_guardan_en_cache(cliente_admin):
    respuesta = cliente_admin.get(reverse("pacientes:lista"))
    assert "no-store" in respuesta["Cache-Control"]
    assert respuesta["Pragma"] == "no-cache"


@pytest.fixture
def con_pregunta(admin):
    admin.pregunta_secreta = "MASCOTA"
    admin.set_respuesta_secreta("Firulais")
    admin.save()
    return admin


def test_recuperacion_completa_con_pregunta_secreta(client, con_pregunta):
    r = client.post(reverse("usuarios:recuperar_correo"), {"email": "ADMIN@prueba.gt"})
    assert r.url == reverse("usuarios:recuperar_pregunta")

    r = client.get(reverse("usuarios:recuperar_pregunta"))
    assert "primera mascota" in r.content.decode()

    r = client.post(reverse("usuarios:recuperar_pregunta"), {"respuesta": "firulais"})
    assert r.url == reverse("usuarios:recuperar_nueva")

    nueva = "Otra-clave-segura-1"
    r = client.post(
        reverse("usuarios:recuperar_nueva"), {"password1": nueva, "password2": nueva}
    )
    assert r.url == reverse("login")
    con_pregunta.refresh_from_db()
    assert con_pregunta.check_password(nueva)


def test_recuperacion_con_correo_desconocido(client, db):
    r = client.post(reverse("usuarios:recuperar_correo"), {"email": "nadie@prueba.gt"})
    assert r.status_code == 200
    assert "No se encontró una cuenta" in r.content.decode()


def test_recuperacion_con_respuesta_incorrecta(client, con_pregunta):
    client.post(reverse("usuarios:recuperar_correo"), {"email": "admin@prueba.gt"})
    r = client.post(reverse("usuarios:recuperar_pregunta"), {"respuesta": "michi"})
    assert "La respuesta no es correcta" in r.content.decode()


def test_no_se_salta_la_pregunta_secreta(client, con_pregunta):
    client.post(reverse("usuarios:recuperar_correo"), {"email": "admin@prueba.gt"})
    r = client.get(reverse("usuarios:recuperar_nueva"))
    assert r.url == reverse("usuarios:recuperar_correo")


def test_pregunta_sin_haber_indicado_correo(client, db):
    r = client.get(reverse("usuarios:recuperar_pregunta"))
    assert r.url == reverse("usuarios:recuperar_correo")


@pytest.mark.parametrize(
    "clave1, clave2, error",
    [
        ("Clave-larga-1", "Clave-larga-2", "no coinciden"),
        ("corta", "corta", "al menos 8"),
    ],
)
def test_nueva_clave_invalida(client, con_pregunta, clave1, clave2, error):
    client.post(reverse("usuarios:recuperar_correo"), {"email": "admin@prueba.gt"})
    client.post(reverse("usuarios:recuperar_pregunta"), {"respuesta": "firulais"})
    r = client.post(
        reverse("usuarios:recuperar_nueva"), {"password1": clave1, "password2": clave2}
    )
    assert r.status_code == 200
    assert error in r.content.decode()

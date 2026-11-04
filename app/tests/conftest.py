"""Datos de prueba comunes.

Cada prueba recibe una base de datos vacía y crea solo lo que necesita con
estas fixtures, sin depender de ``manage.py seed`` ni de la fecha del día.
"""
from datetime import date, time

import pytest

from agenda.models import Cita, HorarioDisponibilidad
from catalogo.models import Especialidad, Odontologo, Procedimiento, UnidadDental
from pacientes.models import Paciente
from usuarios.models import Rol, Usuario

CLAVE = 'Clave-de-prueba-2026'

# Lunes hábil fijo, para que ninguna prueba dependa del día en que se ejecuta.
LUNES = date(2030, 1, 7)

MODULOS = ['usuarios', 'pacientes', 'catalogos', 'agenda', 'clinico',
           'finanzas', 'inteligencia', 'reportes']


@pytest.fixture(autouse=True)
def _hosts_de_prueba(settings):
    settings.ALLOWED_HOSTS = ['testserver']


def crear_rol(nombre, modulos=(), solo_lectura=False, escritura_clinica=False):
    permisos = {f'puede_{m}': m in modulos for m in MODULOS}
    return Rol.objects.create(nombre=nombre, solo_lectura=solo_lectura,
                              escritura_clinica=escritura_clinica, **permisos)


def crear_usuario(email, rol=None, **extra):
    usuario = Usuario.objects.create_user(username=email, email=email,
                                          password=CLAVE, rol=rol, **extra)
    return usuario


@pytest.fixture
def rol_admin(db):
    return crear_rol('Administrador', MODULOS)


@pytest.fixture
def rol_recepcion(db):
    return crear_rol('Recepcionista', ['pacientes', 'agenda', 'finanzas'])


@pytest.fixture
def rol_consulta(db):
    return crear_rol('Consulta', ['pacientes', 'agenda'], solo_lectura=True)


@pytest.fixture
def rol_odontologo(db):
    return crear_rol('Odontólogo', ['pacientes', 'agenda', 'clinico'],
                     solo_lectura=True, escritura_clinica=True)


@pytest.fixture
def admin(rol_admin):
    return crear_usuario('admin@prueba.gt', rol_admin, first_name='Ana', last_name='Admin')


@pytest.fixture
def recepcionista(rol_recepcion):
    return crear_usuario('recepcion@prueba.gt', rol_recepcion)


@pytest.fixture
def consulta(rol_consulta):
    return crear_usuario('consulta@prueba.gt', rol_consulta)


@pytest.fixture
def cliente_admin(client, admin):
    client.force_login(admin)
    return client


@pytest.fixture
def cliente_recepcion(client, recepcionista):
    client.force_login(recepcionista)
    return client


@pytest.fixture
def cliente_consulta(client, consulta):
    client.force_login(consulta)
    return client


@pytest.fixture
def especialidad(db):
    return Especialidad.objects.create(nombre='Odontología general')


@pytest.fixture
def procedimiento(especialidad):
    return Procedimiento.objects.create(
        codigo='PROC-001', nombre='Profilaxis', especialidad=especialidad,
        duracion_promedio_min=30, precio=150)


@pytest.fixture
def odontologo(especialidad):
    odo = Odontologo.objects.create(nombres='Carlos', apellidos='Pérez',
                                    colegiado='CD-1000', especialidad=especialidad)
    HorarioDisponibilidad.objects.create(odontologo=odo, dia_semana='LUN',
                                         hora_inicio=time(8, 0), hora_fin=time(12, 0))
    return odo


@pytest.fixture
def unidades(db):
    return [UnidadDental.objects.create(codigo='SIL-01', nombre='Sillón 1'),
            UnidadDental.objects.create(codigo='SIL-02', nombre='Sillón 2')]


@pytest.fixture
def paciente(db):
    return Paciente.objects.create(codigo='PAC-0001', nombres='María José',
                                   apellidos='López García', telefono='5555-1234')


@pytest.fixture
def cita(paciente, odontologo, procedimiento, unidades):
    return Cita.objects.create(
        paciente=paciente, odontologo=odontologo, procedimiento=procedimiento,
        unidad=unidades[0], fecha=LUNES, hora_inicio_programada=time(9, 0),
        hora_fin_programada=time(9, 30), duracion_asignada_min=30)

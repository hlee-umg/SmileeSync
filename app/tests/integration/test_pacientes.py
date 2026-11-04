"""Integración: CRUD de pacientes con auditoría y borrado lógico."""
import pytest
from django.urls import reverse

from pacientes.models import AntecedenteMedico, HistorialPaciente, Paciente

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def datos_paciente(**cambios):
    datos = {'codigo': 'PAC-0002', 'nombres': 'Juan Carlos', 'apellidos': 'Ramírez',
             'fecha_nacimiento': '1990-05-10', 'sexo': 'M', 'telefono': '5555-0000',
             'email': 'juan@correo.gt', 'direccion': 'Zona 1, Guatemala'}
    datos.update(cambios)
    return datos


def test_crear_paciente_registra_auditoria(cliente_recepcion):
    r = cliente_recepcion.post(reverse('pacientes:crear'), datos_paciente())
    paciente = Paciente.objects.get(codigo='PAC-0002')
    assert r.url == reverse('pacientes:ficha', args=[paciente.pk])
    auditoria = HistorialPaciente.objects.get(paciente_ref=paciente.pk)
    assert auditoria.accion == 'CREACION'
    assert auditoria.realizado_por == 'recepcion@prueba.gt'


def test_formulario_nuevo_propone_el_siguiente_codigo(cliente_recepcion, paciente):
    r = cliente_recepcion.get(reverse('pacientes:crear'))
    assert f'PAC-{paciente.pk + 1:04d}' in r.content.decode()


@pytest.mark.parametrize('campo, valor, mensaje', [
    ('nombres', 'Juan3', 'solo puede contener letras'),
    ('email', 'juan@', 'usuario@dominio.com'),
    ('telefono', 'abc', 'solo puede contener números'),
    ('fecha_nacimiento', '2999-01-01', 'posterior al día de hoy'),
    ('fecha_nacimiento', '1850-01-01', 'Verifique la fecha'),
    ('codigo', 'PAC-0001', 'Ya existe un paciente'),
])
def test_crear_paciente_con_datos_invalidos(cliente_recepcion, paciente, campo, valor, mensaje):
    r = cliente_recepcion.post(reverse('pacientes:crear'), datos_paciente(**{campo: valor}))
    assert r.status_code == 200
    assert mensaje in r.content.decode()
    assert Paciente.objects.count() == 1


def test_editar_paciente_actualiza_y_audita(cliente_recepcion, paciente):
    datos = datos_paciente(codigo='PAC-0001', nombres='María Fernanda')
    r = cliente_recepcion.post(reverse('pacientes:editar', args=[paciente.pk]), datos)
    assert r.status_code == 302
    paciente.refresh_from_db()
    assert paciente.nombres == 'María Fernanda'
    assert HistorialPaciente.objects.filter(accion='ACTUALIZACION').count() == 1


@pytest.mark.regression
@pytest.mark.xfail(strict=True, reason='BUG-02: la auditoría de edición guarda los datos '
                                       'nuevos en lugar del estado previo. Pendiente.')
def test_auditoria_de_edicion_guarda_el_nombre_previo(cliente_recepcion, paciente):
    datos = datos_paciente(codigo='PAC-0001', nombres='María Fernanda')
    cliente_recepcion.post(reverse('pacientes:editar', args=[paciente.pk]), datos)
    registro = HistorialPaciente.objects.get(accion='ACTUALIZACION')
    assert registro.nombre_completo == 'María José López García'


def test_formulario_de_edicion_carga_los_datos(cliente_recepcion, paciente):
    r = cliente_recepcion.get(reverse('pacientes:editar', args=[paciente.pk]))
    assert 'María José' in r.content.decode()


def test_desactivar_es_borrado_logico(cliente_recepcion, paciente):
    cliente_recepcion.post(reverse('pacientes:estado', args=[paciente.pk]))
    paciente.refresh_from_db()
    assert paciente.estado is False
    assert Paciente.objects.filter(pk=paciente.pk).exists()
    assert HistorialPaciente.objects.get().accion == 'DESACTIVACION'

    cliente_recepcion.post(reverse('pacientes:estado', args=[paciente.pk]))
    paciente.refresh_from_db()
    assert paciente.estado is True


def test_cambiar_estado_por_get_no_modifica(cliente_recepcion, paciente):
    cliente_recepcion.get(reverse('pacientes:estado', args=[paciente.pk]))
    paciente.refresh_from_db()
    assert paciente.estado is True


def test_lista_oculta_inactivos_salvo_que_se_pidan(cliente_recepcion, paciente):
    Paciente.objects.create(codigo='PAC-0009', nombres='Pedro', apellidos='Inactivo',
                            estado=False)
    r = cliente_recepcion.get(reverse('pacientes:lista'))
    assert 'Inactivo' not in r.content.decode()
    r = cliente_recepcion.get(reverse('pacientes:lista'), {'inactivos': '1'})
    assert 'Inactivo' in r.content.decode()


@pytest.mark.parametrize('busqueda', ['López', 'pac-0001', '5555-1234'])
def test_buscar_paciente(cliente_recepcion, paciente, busqueda):
    r = cliente_recepcion.get(reverse('pacientes:lista'), {'q': busqueda})
    assert paciente in r.context['pacientes']


def test_buscar_sin_resultados(cliente_recepcion, paciente):
    r = cliente_recepcion.get(reverse('pacientes:lista'), {'q': 'zzz'})
    assert list(r.context['pacientes']) == []


def test_agregar_y_quitar_antecedente(cliente_recepcion, paciente):
    url = reverse('pacientes:ficha', args=[paciente.pk])
    cliente_recepcion.post(url, {'tipo': 'Alergia', 'descripcion': 'Alergia a la penicilina'})
    antecedente = AntecedenteMedico.objects.get(paciente=paciente)
    assert 'penicilina' in cliente_recepcion.get(url).content.decode()

    cliente_recepcion.post(reverse('pacientes:quitar_antecedente', args=[antecedente.pk]))
    antecedente.refresh_from_db()
    assert antecedente.estado is False


def test_antecedente_demasiado_corto(cliente_recepcion, paciente):
    r = cliente_recepcion.post(reverse('pacientes:ficha', args=[paciente.pk]),
                               {'tipo': 'Alergia', 'descripcion': 'x'})
    assert 'al menos cinco caracteres' in r.content.decode()
    assert not AntecedenteMedico.objects.exists()


def test_ficha_de_paciente_inexistente_es_404(cliente_recepcion):
    assert cliente_recepcion.get(reverse('pacientes:ficha', args=[999])).status_code == 404

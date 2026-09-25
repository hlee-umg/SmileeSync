"""Verifica el control de acceso por rol: módulos y escritura."""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client                                    # noqa: E402
from django.urls import reverse                                   # noqa: E402
from usuarios.models import Usuario                               # noqa: E402
from agenda.models import Cita                                    # noqa: E402
from pacientes.models import Paciente                             # noqa: E402

ok = fallo = 0


def probar(titulo, condicion, detalle=''):
    global ok, fallo
    if condicion:
        ok += 1
        print(f'  OK    {titulo}')
    else:
        fallo += 1
        print(f'  FALLA {titulo} {detalle}')


cita = Cita.objects.filter(estado=True).exclude(estado_cita='CANCELADA').first()
paciente = Paciente.objects.filter(estado=True).first()

# lectura: debe responder 200 | escritura: debe responder 403
RUTAS_LECTURA = [
    ('agenda:principal', []),
    ('agenda:lista', []),
]
RUTAS_ESCRITURA = [
    ('agenda:crear', []),
    ('agenda:editar', [cita.pk]),
    ('agenda:tiempos', [cita.pk]),
]

PERFILES = [
    ('admin@smileesync.local', 'Administrador', False),
    ('recepcion@smileesync.local', 'Recepcionista', False),
    ('cgiron@smileesync.local', 'Odontólogo', True),
]

for correo, etiqueta, esperado_solo_consulta in PERFILES:
    u = Usuario.objects.get(email=correo)
    print(f'\n=== {etiqueta} ({correo}) ===')
    probar('es_solo_consulta coincide con lo esperado',
           u.es_solo_consulta == esperado_solo_consulta,
           f'obtenido={u.es_solo_consulta}')

    c = Client()
    c.force_login(u)

    for nombre, args in RUTAS_LECTURA:
        r = c.get(reverse(nombre, args=args))
        probar(f'{nombre} responde 200 (lectura)', r.status_code == 200, r.status_code)

    for nombre, args in RUTAS_ESCRITURA:
        r = c.get(reverse(nombre, args=args))
        if esperado_solo_consulta:
            probar(f'{nombre} bloqueado con 403', r.status_code == 403, r.status_code)
        else:
            probar(f'{nombre} permitido (200)', r.status_code == 200, r.status_code)

    # El POST también debe quedar bloqueado, no solo el enlace de la plantilla
    r = c.post(reverse('agenda:cancelar', args=[cita.pk]))
    if esperado_solo_consulta:
        probar('POST de cancelar bloqueado con 403', r.status_code == 403, r.status_code)
    else:
        probar('POST de cancelar permitido', r.status_code in (200, 302), r.status_code)

    # Los botones no deben aparecer en la plantilla para un rol de consulta
    cuerpo = c.get(reverse('agenda:lista')).content.decode()
    hay_boton = 'Nueva cita' in cuerpo
    probar('el botón "Nueva cita" ' + ('NO aparece' if esperado_solo_consulta else 'aparece'),
           hay_boton != esperado_solo_consulta)

print('\n=== Módulo sin acceso ===')
asistente = Usuario.objects.filter(rol__nombre='Asistente').first()
if asistente is None:
    from usuarios.models import Rol
    asistente = Usuario.objects.create_user(
        'asistente@smileesync.local', 'asistente@smileesync.local', 'Asistente123!',
        first_name='Ana', last_name='Asistente')
    asistente.rol = Rol.objects.get(nombre='Asistente')
    asistente.save()
c = Client()
c.force_login(asistente)
probar('el asistente entra al módulo Principal',
       c.get(reverse('agenda:principal')).status_code == 200)
probar('el asistente no entra a pacientes (403)',
       c.get(reverse('pacientes:lista')).status_code == 403)
probar('el asistente no entra a usuarios (403)',
       c.get(reverse('usuarios:lista')).status_code == 403)
probar('el asistente no puede crear citas (403)',
       c.get(reverse('agenda:crear')).status_code == 403)

print('\n=== Regresión: el administrador conserva todo ===')
c = Client()
c.force_login(Usuario.objects.get(email='admin@smileesync.local'))
for nombre, args in [('pacientes:lista', []), ('pacientes:editar', [paciente.pk]),
                     ('catalogo:lista', ['procedimientos']), ('usuarios:lista', []),
                     ('usuarios:crear', [])]:
    r = c.get(reverse(nombre, args=args))
    probar(f'{nombre} responde 200', r.status_code == 200, r.status_code)

print(f'\n=== {ok} correctas, {fallo} fallidas ===')

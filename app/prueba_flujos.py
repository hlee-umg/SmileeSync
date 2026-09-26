"""Recorre de punta a punta los flujos candidatos para la presentación."""
import os
from datetime import timedelta

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS',
                      'testserver,localhost,127.0.0.1')
django.setup()

from django.test import Client                                    # noqa: E402
from django.urls import reverse                                   # noqa: E402
from django.utils import timezone                                 # noqa: E402
from usuarios.models import Usuario, HistorialUsuario             # noqa: E402
from agenda.models import Cita, HistorialCita                     # noqa: E402
from catalogo.models import Odontologo, Procedimiento, Especialidad  # noqa: E402
from pacientes.models import Paciente                             # noqa: E402
from inteligencia.models import DatoEntrenamiento                 # noqa: E402

ok = fallo = 0


def probar(t, c, d=''):
    global ok, fallo
    if c:
        ok += 1
        print(f'  OK    {t}')
    else:
        fallo += 1
        print(f'  FALLA {t} {d}')


hoy = timezone.localdate()
admin = Usuario.objects.get(email='admin@smileesync.local')

print('FLUJO 1 — Acceso, roles y recuperación de contraseña')
c = Client()
r = c.post(reverse('login'), {'username': 'admin@smileesync.local',
                              'password': '***REMOVED***'}, follow=True)
probar('inicio de sesión con correo', r.status_code == 200 and
       'Administrador' in r.content.decode())
cx = Client()
r = cx.post(reverse('login'), {'username': 'admin@smileesync.local',
                               'password': 'incorrecta'})
probar('credenciales incorrectas no entran',
       not r.wsgi_request.user.is_authenticated and
       'incorrectos' in r.content.decode())

c2 = Client()
r = c2.post(reverse('usuarios:recuperar_correo'),
            {'email': 'admin@smileesync.local'}, follow=True)
probar('recuperación: acepta el correo y pide la pregunta',
       r.status_code == 200 and 'mascota' in r.content.decode().lower())
r = c2.post(reverse('usuarios:recuperar_pregunta'), {'respuesta': 'firulais'},
            follow=True)
probar('recuperación: acepta la respuesta secreta',
       r.status_code == 200 and 'contrase' in r.content.decode().lower())
r = c2.post(reverse('usuarios:recuperar_nueva'),
            {'password1': 'NuevaClave123!', 'password2': 'NuevaClave123!'},
            follow=True)
probar('recuperación: cambia la contraseña', r.status_code == 200)
c3 = Client()
entro = c3.login(username='admin@smileesync.local', password='NuevaClave123!')
probar('la contraseña nueva funciona', entro)
admin.set_password('***REMOVED***')
admin.save()

print('\nFLUJO 2 — Programar una cita con recomendación')
c = Client()
c.force_login(admin)
odo = Odontologo.objects.filter(estado=True, horarios__estado=True).distinct().first()
proc = Procedimiento.objects.filter(estado=True).order_by('duracion_promedio_min').first()
pac = Paciente.objects.filter(estado=True).first()
siguiente = hoy + timedelta(days=1)
while siguiente.weekday() > 4:
    siguiente += timedelta(days=1)
# Se pide la semana del próximo día hábil: la semana en curso puede no tener
# ninguno (un sábado) y entonces no hay espacios libres que proponer.
semana = siguiente - timedelta(days=siguiente.weekday())
r = c.get(reverse('agenda:principal'), {'odontologo': odo.pk, 'procedimiento': proc.pk,
                                        'semana': semana.isoformat()})
cuerpo = r.content.decode()
probar('el calendario marca espacios disponibles', 'class="hueco-sugerido' in cuerpo)
probar('muestra la duración estimada', 'min estimados' in cuerpo)

r = c.get(reverse('agenda:crear'), {'fecha': siguiente.isoformat(), 'hora': '10:00',
                                    'odontologo': odo.pk, 'procedimiento': proc.pk})
probar('el formulario abre precargado', r.status_code == 200 and
       f'value="{siguiente.isoformat()}"' in r.content.decode())

r = c.get(reverse('agenda:estimar'), {'procedimiento': proc.pk, 'odontologo': odo.pk,
                                      'fecha': siguiente.isoformat(),
                                      'hora': '10:00', 'piezas': 1})
probar('el endpoint de estimación responde en línea',
       r.status_code == 200 and 'duracion' in r.json())
if r.status_code == 200:
    print(f'        estimación: {r.json()}')

antes = Cita.objects.count()
r = c.post(reverse('agenda:crear'), {
    'paciente': pac.pk, 'odontologo': odo.pk, 'procedimiento': proc.pk,
    'fecha': siguiente.isoformat(), 'hora_inicio_programada': '10:00',
    'duracion_asignada_min': proc.duracion_promedio_min, 'num_piezas': 1,
    'observaciones': 'Demostración'}, follow=True)
probar('la cita se crea', Cita.objects.count() == antes + 1)
nueva = Cita.objects.order_by('-id').first()
probar('queda registro de auditoría',
       HistorialCita.objects.filter(cita_ref=nueva.pk, accion='CREACION').exists())

print('\nFLUJO 3 — El sistema impide errores de agenda')
r = c.post(reverse('agenda:crear'), {
    'paciente': pac.pk, 'odontologo': odo.pk, 'procedimiento': proc.pk,
    'fecha': siguiente.isoformat(), 'hora_inicio_programada': '10:00',
    'duracion_asignada_min': proc.duracion_promedio_min, 'num_piezas': 1})
probar('rechaza el traslape y nombra la cita en conflicto',
       'traslapa' in r.content.decode())
r = c.post(reverse('agenda:crear'), {
    'paciente': pac.pk, 'odontologo': odo.pk, 'procedimiento': proc.pk,
    'fecha': siguiente.isoformat(), 'hora_inicio_programada': '22:00',
    'duracion_asignada_min': 30, 'num_piezas': 1})
probar('rechaza fuera del horario de atención',
       'fuera del horario' in r.content.decode())
r = c.post(reverse('agenda:crear'), {
    'paciente': pac.pk, 'odontologo': odo.pk, 'procedimiento': proc.pk,
    'fecha': (hoy - timedelta(days=3)).isoformat(),
    'hora_inicio_programada': '10:00', 'duracion_asignada_min': 30, 'num_piezas': 1})
probar('rechaza una fecha pasada', 'fecha pasada' in r.content.decode())

print('\nFLUJO 4 — Cerrar el ciclo: registrar la atención alimenta el modelo')
datos_antes = DatoEntrenamiento.objects.count()
r = c.post(reverse('agenda:tiempos', args=[nueva.pk]),
           {'hora_inicio_real': '10:05', 'hora_fin_real': '10:40'}, follow=True)
nueva.refresh_from_db()
probar('la cita queda atendida', nueva.estado_cita == 'ATENDIDA', nueva.estado_cita)
probar('calcula la duración real', nueva.duracion_real_min == 35, nueva.duracion_real_min)
probar('el registro entra al conjunto de entrenamiento',
       DatoEntrenamiento.objects.count() == datos_antes + 1)
cuerpo = c.get(reverse('agenda:detalle', args=[nueva.pk])).content.decode()
probar('el detalle muestra la desviación', 'Desviación' in cuerpo)

print('\nFLUJO 5 — Alta de odontólogo y sus horarios')
esp = Especialidad.objects.filter(estado=True).first()
r = c.post(reverse('catalogo:crear', args=['odontologos']), {
    'nombres': 'Demo', 'apellidos': 'Presentación', 'colegiado': 'CD-DEMO',
    'especialidad': esp.pk, 'telefono': '5555 5555'}, follow=True)
demo = Odontologo.objects.filter(colegiado='CD-DEMO').first()
probar('se crea el odontólogo', demo is not None)
if demo:
    cuerpo = c.get(reverse('catalogo:lista', args=['odontologos'])).content.decode()
    probar('el listado lo marca como pendiente de configurar', 'Configurar' in cuerpo)
    r = c.post(reverse('agenda:crear'), {
        'paciente': pac.pk, 'odontologo': demo.pk, 'procedimiento': proc.pk,
        'fecha': siguiente.isoformat(), 'hora_inicio_programada': '09:00',
        'duracion_asignada_min': 30, 'num_piezas': 1})
    probar('sin horarios, el sistema rechaza sus citas',
           'no tiene horario de atención' in r.content.decode())
    r = c.post(reverse('agenda:horarios', args=[demo.pk]),
               {'dia_semana': 'LUN', 'hora_inicio': '08:00', 'hora_fin': '12:00',
                'replicar': 'on'}, follow=True)
    probar('se configuran las franjas de lunes a viernes',
           demo.horarios.filter(estado=True).count() == 5)
    r = c.post(reverse('agenda:crear'), {
        'paciente': pac.pk, 'odontologo': demo.pk, 'procedimiento': proc.pk,
        'fecha': siguiente.isoformat(), 'hora_inicio_programada': '09:00',
        'duracion_asignada_min': 30, 'num_piezas': 1}, follow=True)
    probar('ahora sí acepta la cita',
           Cita.objects.filter(odontologo=demo).exists())

print('\nFLUJO 6 — Mantenimiento de usuarios con validaciones y auditoría')
r = c.post(reverse('usuarios:crear'), {
    'username': 'demo1', 'first_name': 'Ana3', 'last_name': 'Pérez',
    'email': 'demo@correo.com', 'rol': admin.rol_id,
    'password1': 'Clave12345!', 'password2': 'Clave12345!'})
probar('rechaza números en el nombre', 'solo puede contener letras' in r.content.decode())
r = c.post(reverse('usuarios:crear'), {
    'username': 'demo1', 'first_name': 'Ana', 'last_name': 'Pérez',
    'email': 'sin-arroba', 'rol': admin.rol_id,
    'password1': 'Clave12345!', 'password2': 'Clave12345!'})
probar('rechaza un correo inválido', 'usuario@dominio.com' in r.content.decode())
r = c.post(reverse('usuarios:crear'), {
    'username': 'demo1', 'first_name': 'María José', 'last_name': 'López-García',
    'email': 'demo@correo.com', 'rol': admin.rol_id,
    'pregunta_secreta': 'CIUDAD', 'respuesta_secreta': 'guatemala',
    'password1': 'Clave12345!', 'password2': 'Clave12345!'}, follow=True)
creado = Usuario.objects.filter(email='demo@correo.com').first()
probar('acepta nombres compuestos y con guion', creado is not None)
if creado:
    r = c.post(reverse('usuarios:cambiar_estado', args=[creado.pk]), follow=True)
    creado.refresh_from_db()
    probar('el borrado es lógico', creado.estado is False and
           Usuario.objects.filter(pk=creado.pk).exists())
    probar('queda registrado en el historial',
           HistorialUsuario.objects.filter(usuario_ref=creado.pk).exists())
    cuerpo = c.get(reverse('usuarios:historial')).content.decode()
    probar('el historial es consultable en pantalla', 'demo@correo.com' in cuerpo)

print(f'\n=== {ok} correctas, {fallo} fallidas ===')

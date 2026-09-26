"""Verifica la recomendación de bloques sobre el calendario."""
import os
import re
from datetime import datetime, timedelta

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS',
                      'testserver,localhost,127.0.0.1')
django.setup()

from django.test import Client                                    # noqa: E402
from django.urls import reverse                                   # noqa: E402
from django.utils import timezone                                 # noqa: E402
from usuarios.models import Usuario                                # noqa: E402
from agenda.models import Cita, HorarioDisponibilidad              # noqa: E402
from catalogo.models import Odontologo, Procedimiento              # noqa: E402
from agenda.forms import hay_traslape                              # noqa: E402

ok = fallo = 0


def probar(titulo, condicion, detalle=''):
    global ok, fallo
    if condicion:
        ok += 1
        print(f'  OK    {titulo}')
    else:
        fallo += 1
        print(f'  FALLA {titulo} {detalle}')


c = Client()
c.force_login(Usuario.objects.get(email='admin@smileesync.local'))
url = reverse('agenda:principal')
hoy = timezone.localdate()
# La semana que se examina es la que contiene el próximo día hábil completo: la
# semana en curso puede no tener ninguno (un sábado, por ejemplo), y sin días
# futuros no hay espacios que sugerir.
_habil = hoy + timedelta(days=1)
while _habil.weekday() > 4:
    _habil += timedelta(days=1)
lunes = _habil - timedelta(days=_habil.weekday())

odo = Odontologo.objects.filter(estado=True, horarios__estado=True).distinct().first()
largo = Procedimiento.objects.filter(estado=True).order_by('-duracion_promedio_min').first()
corto = Procedimiento.objects.filter(estado=True).order_by('duracion_promedio_min').first()

print(f'Odontólogo: {odo} | largo: {largo} ({largo.duracion_promedio_min} min) '
      f'| corto: {corto} ({corto.duracion_promedio_min} min)')

print('\n1. Sin procedimiento no hay sugerencias')
cuerpo = c.get(url, {'semana': lunes.isoformat(), 'odontologo': odo.pk}).content.decode()
probar('no hay huecos sugeridos', 'class="hueco-sugerido' not in cuerpo)
probar('el panel invita a elegir', '¿Dónde cabe este procedimiento?' in cuerpo)

print('\n2. Con procedimiento y odontólogo se marcan los huecos')
cuerpo = c.get(url, {'semana': lunes.isoformat(), 'odontologo': odo.pk,
                     'procedimiento': corto.pk}).content.decode()
probar('aparecen huecos sugeridos', 'class="hueco-sugerido' in cuerpo)
probar('se muestra la duración estimada', 'min estimados' in cuerpo)
plano = re.sub(r'\s+', ' ', cuerpo)
m = re.search(r'(\d+) espacios? disponibles?', plano)
probar('se informa cuántos espacios hay', m is not None)
espacios_corto = int(m.group(1)) if m else 0

print('\n3. Un procedimiento más largo no ofrece más espacios que uno corto')
cuerpo_l = c.get(url, {'semana': lunes.isoformat(), 'odontologo': odo.pk,
                       'procedimiento': largo.pk}).content.decode()
m2 = re.search(r'(\d+) espacios? disponibles?', re.sub(r'\s+', ' ', cuerpo_l))
espacios_largo = int(m2.group(1)) if m2 else 0
probar('el procedimiento largo tiene menos o igual espacios',
       espacios_largo <= espacios_corto, f'{largo.duracion_promedio_min}min='
       f'{espacios_largo} vs {corto.duracion_promedio_min}min={espacios_corto}')

print('\n4. Sin odontólogo se pide elegir uno')
cuerpo_n = c.get(url, {'semana': lunes.isoformat(), 'procedimiento': corto.pk}).content.decode()
probar('avisa que falta el odontólogo', 'Falta el odontólogo' in cuerpo_n)
probar('no marca huecos', 'class="hueco-sugerido' not in cuerpo_n)

print('\n4b. Sin procedimiento se pide elegir uno')
cuerpo_p = c.get(url, {'semana': lunes.isoformat(), 'odontologo': odo.pk}).content.decode()
probar('avisa que falta el procedimiento', 'Falta el procedimiento' in cuerpo_p)
# El panel pide los dos campos en el mismo formulario: cambiar de odontólogo en
# el filtro de arriba no debe descartar el procedimiento ya consultado.
probar('el filtro del calendario conserva el procedimiento consultado',
       f'name="procedimiento" value="{corto.pk}"' in cuerpo_n,
       corto.pk)
probar('el panel ofrece elegir el odontólogo sin salir de él',
       cuerpo_p.count('name="odontologo"') >= 2,
       cuerpo_p.count('name="odontologo"'))

print('\n5. Los huecos propuestos son realmente válidos')
cuerpo = c.get(url, {'semana': lunes.isoformat(), 'odontologo': odo.pk,
                     'procedimiento': corto.pk}).content.decode()
propuestas = re.findall(
    r'href="/citas/nueva/\?fecha=(\d{4}-\d{2}-\d{2})&hora=(\d{2}:\d{2})[^"]*"\s+'
    r'title="Cabe una cita de (\d+) min', cuerpo)
probar('se extrajeron propuestas del HTML', len(propuestas) > 0, len(propuestas))

DIAS = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
invalidas = []
for fecha_txt, hora_txt, dur_txt in propuestas:
    fecha = datetime.strptime(fecha_txt, '%Y-%m-%d').date()
    ini = datetime.strptime(hora_txt, '%H:%M').time()
    fin = (datetime.combine(fecha, ini) + timedelta(minutes=int(dur_txt))).time()
    franjas = HorarioDisponibilidad.objects.filter(
        odontologo=odo, dia_semana=DIAS[fecha.weekday()], estado=True)
    cabe = any(f.hora_inicio <= ini and fin <= f.hora_fin for f in franjas)
    choca = any(hay_traslape(ini, fin, c2.hora_inicio_programada, c2.hora_fin_programada)
                for c2 in Cita.objects.filter(odontologo=odo, fecha=fecha, estado=True)
                .exclude(estado_cita='CANCELADA'))
    pasado = fecha < hoy
    if not cabe or choca or pasado:
        invalidas.append((fecha_txt, hora_txt,
                          f'cabe={cabe} choca={choca} pasado={pasado}'))
probar('todas las propuestas caben en una franja y no se traslapan',
       not invalidas, invalidas[:3])

print('\n6. La propuesta abre el formulario ya cargado')
if propuestas:
    f_txt, h_txt, _ = propuestas[0]
    r = c.get(reverse('agenda:crear'), {'fecha': f_txt, 'hora': h_txt,
                                        'odontologo': odo.pk,
                                        'procedimiento': corto.pk})
    cuerpo_f = r.content.decode()
    probar('el formulario responde 200', r.status_code == 200, r.status_code)
    probar('trae la fecha', f'value="{f_txt}"' in cuerpo_f)
    probar('trae la hora', f'value="{h_txt}"' in cuerpo_f)
    probar('trae el procedimiento', f'value="{corto.pk}" selected' in cuerpo_f)

print('\n7. Y la cita propuesta se puede guardar sin errores de validación')
if propuestas:
    futuras = [p for p in propuestas
               if datetime.strptime(p[0], '%Y-%m-%d').date() >= hoy]
    if futuras:
        f_txt, h_txt, dur_txt = futuras[0]
        from pacientes.models import Paciente
        pac = Paciente.objects.filter(estado=True).first()
        antes = Cita.objects.count()
        r = c.post(reverse('agenda:crear'), {
            'paciente': pac.pk, 'odontologo': odo.pk, 'procedimiento': corto.pk,
            'fecha': f_txt, 'hora_inicio_programada': h_txt,
            'duracion_asignada_min': dur_txt, 'num_piezas': 1, 'observaciones': ''},
            follow=True)
        probar('la cita propuesta se creó', Cita.objects.count() == antes + 1,
               [l.strip() for l in r.content.decode().splitlines()
                if 'text-danger' in l][:2])
    else:
        print('  (omitida: no hay propuestas en días futuros)')

print('\n8. Vista diaria con recomendación')
# el siguiente día hábil: el seed solo carga horarios de lunes a viernes
dia_habil = hoy + timedelta(days=1)
while dia_habil.weekday() > 4:
    dia_habil += timedelta(days=1)
r = c.get(url, {'vista': 'dia', 'fecha': dia_habil.isoformat(),
                'odontologo': odo.pk, 'procedimiento': corto.pk})
print(f'  (día evaluado: {dia_habil})')
probar('responde 200', r.status_code == 200, r.status_code)
probar('marca huecos también en la vista diaria',
       'class="hueco-sugerido' in r.content.decode())

print(f'\n=== {ok} correctas, {fallo} fallidas ===')

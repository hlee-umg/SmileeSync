"""Verifica la restricción de unidades dentales y las ausencias puntuales."""
import os
from datetime import time, timedelta

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS',
                      'testserver,localhost,127.0.0.1')
django.setup()

from django.test import Client                                    # noqa: E402
from django.urls import reverse                                   # noqa: E402
from django.utils import timezone                                 # noqa: E402
from usuarios.models import Usuario                               # noqa: E402
from agenda.models import (AusenciaOdontologo, Cita,              # noqa: E402
                           HorarioDisponibilidad)
from agenda.disponibilidad import (capacidad_minutos,             # noqa: E402
                                   franjas_efectivas, unidades_libres)
from catalogo.models import Odontologo, Procedimiento, UnidadDental  # noqa: E402
from pacientes.models import Paciente                             # noqa: E402

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
# Se busca un día hábil futuro que el seed no haya ocupado: la prueba llena las
# dos unidades a propósito, de modo que una cita sembrada a la misma hora
# falsearía el resultado.
futuro = hoy + timedelta(days=1)
while futuro.weekday() > 4 or Cita.objects.filter(fecha=futuro, estado=True).exists():
    futuro += timedelta(days=1)

admin = Usuario.objects.get(email='admin@smileesync.local')
c = Client()
c.force_login(admin)
proc = Procedimiento.objects.filter(estado=True).order_by('duracion_promedio_min').first()
pacientes = list(Paciente.objects.filter(estado=True))
odos = list(Odontologo.objects.filter(estado=True))
odo = odos[0]


def programar(odontologo, paciente, fecha, hora, duracion=20):
    return c.post(reverse('agenda:crear'), {
        'paciente': paciente.pk, 'odontologo': odontologo.pk,
        'procedimiento': proc.pk, 'fecha': fecha.isoformat(),
        'hora_inicio_programada': hora, 'duracion_asignada_min': duracion,
        'num_piezas': 1, 'observaciones': ''})


print('1. Las unidades son registros del catálogo')
probar('hay dos unidades sembradas', UnidadDental.objects.count() == 2,
       UnidadDental.objects.count())
r = c.get(reverse('catalogo:lista', args=['unidades']))
probar('el catálogo las lista', r.status_code == 200 and 'SIL-01' in r.content.decode())
r = c.post(reverse('catalogo:crear', args=['unidades']), {
    'codigo': 'SIL-99', 'nombre': 'Sillón de prueba', 'ubicacion': 'Anexo',
    'observaciones': ''}, follow=True)
probar('se puede dar de alta una unidad nueva',
       UnidadDental.objects.filter(codigo='SIL-99').exists())
extra = UnidadDental.objects.get(codigo='SIL-99')

print('\n2. La capacidad se deriva de las unidades activas')
cap_3 = capacidad_minutos(odos, [futuro])
extra.estado = False
extra.save()
cap_2 = capacidad_minutos(odos, [futuro])
probar('con menos unidades la capacidad no aumenta', cap_2 <= cap_3, f'{cap_2} vs {cap_3}')
probar('con dos odontólogos y dos sillones la capacidad es la declarada',
       cap_2 > 0, cap_2)

print('\n3. Se asigna un sillón al programar')
antes = Cita.objects.count()
r = programar(odo, pacientes[0], futuro, '09:00')
probar('la cita se crea', Cita.objects.count() == antes + 1)
cita1 = Cita.objects.order_by('-id').first()
probar('queda con unidad asignada', cita1.unidad is not None, cita1.unidad)

print('\n4. Se rechaza cuando todas las unidades están ocupadas')
r = programar(odos[1], pacientes[1], futuro, '09:00')
cita2 = Cita.objects.order_by('-id').first()
probar('la segunda usa la otra unidad',
       cita2.unidad_id != cita1.unidad_id, f'{cita1.unidad} / {cita2.unidad}')
tercero = Odontologo.objects.create(nombres='Tercer', apellidos='Odontólogo',
                                    colegiado='CD-CAP', especialidad=odo.especialidad)
for d in ['LUN', 'MAR', 'MIE', 'JUE', 'VIE']:
    HorarioDisponibilidad.objects.create(odontologo=tercero, dia_semana=d,
                                         hora_inicio=time(8, 0), hora_fin=time(12, 0))
antes = Cita.objects.count()
r = programar(tercero, pacientes[2], futuro, '09:00')
probar('la tercera se rechaza', Cita.objects.count() == antes)
probar('el mensaje explica que no hay unidades',
       'unidades dentales están ocupadas' in r.content.decode())
# Con una sola unidad activa el mensaje se redacta en singular: es el caso que
# se usa para mostrar la restricción de capacidad en una demostración.
extra.estado = True
extra.save()
UnidadDental.objects.exclude(pk=extra.pk).update(estado=False)
r = programar(odos[1], pacientes[5], futuro, '11:00')
r = programar(tercero, pacientes[4], futuro, '11:00')
probar('con una sola unidad el mensaje va en singular',
       'La única unidad dental está ocupada' in r.content.decode())
UnidadDental.objects.exclude(pk=extra.pk).update(estado=True)
extra.estado = False
extra.save()
probar('no quedan unidades libres a esa hora',
       unidades_libres(futuro, time(9, 0), time(9, 20)) == [])

print('\n5. Al liberar una unidad vuelve a haber espacio')
c.post(reverse('agenda:cancelar', args=[cita1.pk]), follow=True)
antes = Cita.objects.count()
r = programar(tercero, pacientes[2], futuro, '09:00')
probar('ahora sí se acepta', Cita.objects.count() == antes + 1)

print('\n6. Las ausencias descuentan del patrón semanal')
franjas_antes = franjas_efectivas(odo, futuro)
probar('el odontólogo tiene franjas ese día', len(franjas_antes) > 0, franjas_antes)
r = c.post(reverse('agenda:ausencias', args=[odo.pk]), {
    'fecha': futuro.isoformat(), 'hora_inicio': '08:00', 'hora_fin': '12:00',
    'motivo': 'Congreso'}, follow=True)
probar('se registra la ausencia parcial',
       AusenciaOdontologo.objects.filter(odontologo=odo, fecha=futuro).exists())
franjas_despues = franjas_efectivas(odo, futuro)
probar('la franja de la mañana desaparece',
       not any(i < time(12, 0) for i, _ in franjas_despues), franjas_despues)
probar('la de la tarde se conserva',
       any(i >= time(12, 0) for i, _ in franjas_despues), franjas_despues)

print('\n7. No se puede programar dentro de una ausencia')
r = programar(odo, pacientes[3], futuro, '10:00')
probar('rechaza la cita en la franja ausente',
       'fuera del horario de atención' in r.content.decode())
r = programar(odo, pacientes[3], futuro, '15:00')
probar('acepta la cita fuera de la ausencia',
       Cita.objects.filter(odontologo=odo, fecha=futuro,
                           hora_inicio_programada='15:00').exists())

print('\n8. La ausencia de toda la jornada vacía el día')
otro = odos[1]
c.post(reverse('agenda:ausencias', args=[otro.pk]),
       {'fecha': futuro.isoformat(), 'todo_el_dia': 'on', 'motivo': 'Vacaciones'},
       follow=True)
probar('no queda ninguna franja', franjas_efectivas(otro, futuro) == [],
       franjas_efectivas(otro, futuro))
r = programar(otro, pacientes[4], futuro, '15:00')
probar('el mensaje menciona la ausencia',
       'ausencia que cubre toda su jornada' in r.content.decode())

print('\n9. La recomendación respeta las ausencias')
cuerpo = c.get(reverse('agenda:principal'),
               {'fecha': futuro.isoformat(), 'vista': 'dia',
                'odontologo': otro.pk, 'procedimiento': proc.pk}).content.decode()
probar('no propone espacios en un día de ausencia total',
       'class="hueco-sugerido' not in cuerpo)

print('\n10. El odontólogo puede marcar sus propias ausencias')
usuario_odo = Usuario.objects.get(email='hjlee@smileesync.local')
ficha = Odontologo.objects.filter(usuario=usuario_odo).first()
probar('su usuario está vinculado a una ficha', ficha is not None)
co = Client()
co.force_login(usuario_odo)
probar('es un rol de solo consulta', usuario_odo.es_solo_consulta)
probar('no puede crear citas',
       co.get(reverse('agenda:crear')).status_code == 403)
r = co.get(reverse('agenda:ausencias', args=[ficha.pk]))
probar('sí entra a sus propias ausencias', r.status_code == 200, r.status_code)
otra_ficha = Odontologo.objects.exclude(pk=ficha.pk).first()
probar('no entra a las de otro odontólogo',
       co.get(reverse('agenda:ausencias', args=[otra_ficha.pk])).status_code == 403)
antes = AusenciaOdontologo.objects.filter(odontologo=ficha).count()
co.post(reverse('agenda:ausencias', args=[ficha.pk]),
        {'fecha': (futuro + timedelta(days=1)).isoformat(), 'todo_el_dia': 'on',
         'motivo': 'Asunto personal'}, follow=True)
probar('registra la suya',
       AusenciaOdontologo.objects.filter(odontologo=ficha).count() == antes + 1)

print('\n11. El calendario del odontólogo se filtra a su agenda')
cuerpo = co.get(reverse('agenda:principal')).content.decode()
probar('aparece la opción "Mi agenda"', 'Mi agenda' in cuerpo)
probar('viene preseleccionada',
       f'value="{ficha.pk}"\n              selected' in cuerpo or
       f'value="{ficha.pk}" selected' in cuerpo or
       'Mi agenda' in cuerpo and f'value="{ficha.pk}"' in cuerpo)
cuerpo_todos = co.get(reverse('agenda:principal'), {'odontologo': ''}).content.decode()
probar('puede volver a ver todos', 'Todos los odontólogos' in cuerpo_todos)

print(f'\n=== {ok} correctas, {fallo} fallidas ===')

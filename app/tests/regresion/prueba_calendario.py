"""Verifica el calendario operable, la vista diaria y la navegación."""

import os
import re

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402
from usuarios.models import Usuario  # noqa: E402
from agenda.models import Cita  # noqa: E402
from catalogo.models import Odontologo  # noqa: E402

ok = fallo = 0


def probar(titulo, condicion, detalle=""):
    global ok, fallo
    if condicion:
        ok += 1
        print(f"  OK    {titulo}")
    else:
        fallo += 1
        print(f"  FALLA {titulo} {detalle}")


admin = Usuario.objects.get(email="admin@smileesync.local")
odontologo_usuario = Usuario.objects.get(email="hjlee@smileesync.local")
c = Client()
c.force_login(admin)
hoy = timezone.localdate()
url = reverse("agenda:principal")

# La rejilla se examina sobre la semana que contiene las citas programadas, no
# sobre la semana en curso: si hoy es sábado o domingo, la semana actual ya no
# tiene días hábiles por delante y el calendario aparece —correctamente— vacío.
cita = (
    Cita.objects.filter(
        fecha__gte=hoy, estado=True, estado_cita__in=["PROGRAMADA", "REPROGRAMADA"]
    )
    .order_by("fecha")
    .first()
)
semana = cita.fecha - timezone.timedelta(days=cita.fecha.weekday())

print("1. Vista semanal")
r = c.get(url, {"semana": semana.isoformat()})
cuerpo = r.content.decode()
probar("responde 200", r.status_code == 200, r.status_code)
probar("muestra la semana", "Semana del" in cuerpo)
probar("hay botones Día y Semana", ">Día</a>" in cuerpo and ">Semana</a>" in cuerpo)
probar("hay botón Hoy", ">Hoy</a>" in cuerpo)
probar(
    "la vista por omisión es la semana en curso",
    "Semana del" in c.get(url).content.decode(),
)

print("\n2. Las citas enlazan a su detalle")
enlaces = re.findall(r'href="(/citas/\d+/)"', cuerpo)
probar("la rejilla contiene enlaces a detalle", len(enlaces) > 0, len(enlaces))
probar(
    "el enlace de una cita de la semana está presente",
    f"/citas/{cita.pk}/" in cuerpo,
    cita.pk,
)

print("\n3. Las casillas libres enlazan a la programación")
m = re.search(
    r'href="/citas/nueva/\?fecha=(\d{4}-\d{2}-\d{2})&hora=(\d{2}:\d{2})"', cuerpo
)
probar("hay enlaces de casilla libre con fecha y hora", m is not None)
if m:
    fecha_casilla, hora_casilla = m.group(1), m.group(2)
    r2 = c.get(reverse("agenda:crear"), {"fecha": fecha_casilla, "hora": hora_casilla})
    cuerpo2 = r2.content.decode()
    probar("el formulario abre con 200", r2.status_code == 200, r2.status_code)
    probar("la fecha viene precargada", f'value="{fecha_casilla}"' in cuerpo2)
    probar("la hora viene precargada", f'value="{hora_casilla}"' in cuerpo2)

print("\n4. El odontólogo del filtro se precarga")
odo = Odontologo.objects.filter(estado=True).first()
r = c.get(url, {"odontologo": odo.pk, "semana": semana.isoformat()})
cuerpo_f = r.content.decode()
probar("el enlace de casilla lleva el odontólogo", f"&odontologo={odo.pk}" in cuerpo_f)
r = c.get(
    reverse("agenda:crear"),
    {"fecha": semana.isoformat(), "hora": "09:00", "odontologo": odo.pk},
)
probar(
    "el formulario preselecciona al odontólogo",
    f'value="{odo.pk}" selected' in r.content.decode(),
)

print("\n5. Vista diaria")
r = c.get(url, {"vista": "dia", "fecha": hoy.isoformat()})
cuerpo_d = r.content.decode()
probar("responde 200", r.status_code == 200, r.status_code)
probar("no muestra el rótulo de semana", "Semana del" not in cuerpo_d)
probar(
    "una sola columna de día",
    cuerpo_d.count('<th class="') <= 2,
    cuerpo_d.count('<th class="'),
)

print("\n6. Navegación")
r = c.get(url, {"vista": "dia", "fecha": hoy.isoformat()})
cuerpo_d = r.content.decode()
maniana = (hoy + timezone.timedelta(days=1)).isoformat()
ayer = (hoy - timezone.timedelta(days=1)).isoformat()
probar("el siguiente apunta a mañana", f"fecha={maniana}" in cuerpo_d, maniana)
probar("el anterior apunta a ayer", f"fecha={ayer}" in cuerpo_d, ayer)
r = c.get(url, {"vista": "dia", "fecha": "no-es-fecha"})
probar("una fecha inválida no rompe la pantalla", r.status_code == 200, r.status_code)

print("\n7. Detalle de la cita")
r = c.get(reverse("agenda:detalle", args=[cita.pk]))
cuerpo_det = r.content.decode()
probar("responde 200", r.status_code == 200, r.status_code)
probar("muestra al paciente", str(cita.paciente) in cuerpo_det)
probar("ofrece registrar la atención", "Registrar la atención" in cuerpo_det)
probar("ofrece reprogramar", "Reprogramar" in cuerpo_det)
probar("ofrece cancelar", "Cancelar la cita" in cuerpo_det)

atendida = Cita.objects.filter(estado_cita="ATENDIDA", estado=True).first()
if atendida:
    cuerpo_at = c.get(reverse("agenda:detalle", args=[atendida.pk])).content.decode()
    probar(
        "una cita atendida no ofrece acciones", "Registrar la atención" not in cuerpo_at
    )
    probar("una cita atendida muestra la desviación", "Desviación" in cuerpo_at)

print("\n8. Un rol de solo consulta no ve acciones ni casillas libres")
c2 = Client()
c2.force_login(odontologo_usuario)
cuerpo_ro = c2.get(url, {"semana": semana.isoformat()}).content.decode()
probar("no aparece el botón Nueva cita", "Nueva cita" not in cuerpo_ro)
probar("no aparecen casillas libres", 'class="casilla-libre"' not in cuerpo_ro)
# el odontólogo ve su propia agenda por omisión, así que se verifica con una
# cita suya; y que pueda cambiar el filtro para ver las de toda la clínica
propia = (
    Cita.objects.filter(odontologo__usuario=odontologo_usuario, estado=True)
    .exclude(estado_cita="CANCELADA")
    .order_by("fecha")
    .first()
)
if propia:
    cuerpo_propia = c2.get(
        url, {"fecha": propia.fecha.isoformat(), "vista": "dia"}
    ).content.decode()
    probar("ve sus propias citas", f"/citas/{propia.pk}/" in cuerpo_propia)
cuerpo_todos = c2.get(
    url, {"odontologo": "", "semana": semana.isoformat()}
).content.decode()
probar("puede ver las de toda la clínica", f"/citas/{cita.pk}/" in cuerpo_todos)
cuerpo_ro_det = c2.get(reverse("agenda:detalle", args=[cita.pk])).content.decode()
probar(
    "el detalle explica que es solo consulta",
    "solo consulta" in cuerpo_ro_det and "Registrar la atención" not in cuerpo_ro_det,
)

print(f"\n=== {ok} correctas, {fallo} fallidas ===")

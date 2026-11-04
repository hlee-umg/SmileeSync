"""Pruebas manuales de la pantalla de horarios de disponibilidad."""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from agenda.models import Cita, HorarioDisponibilidad  # noqa: E402
from catalogo.models import Especialidad, Odontologo  # noqa: E402
from usuarios.models import Usuario  # noqa: E402

from django.utils import timezone as _tz  # noqa: E402


def _hoy():
    return _tz.localdate()


ok = fallo = 0


def probar(titulo, condicion, detalle=""):
    global ok, fallo
    if condicion:
        ok += 1
        print(f"  OK   {titulo}")
    else:
        fallo += 1
        print(f"  FALLA {titulo} {detalle}")


c = Client()
admin = (
    Usuario.objects.filter(is_superuser=True).first()
    or Usuario.objects.filter(rol__nombre__icontains="admin").first()
)
c.force_login(admin)
print(f"Sesión iniciada como {admin.email}\n")

# --- odontólogo nuevo, sin horarios ------------------------------------------
esp = Especialidad.objects.filter(estado=True).first()
nuevo = Odontologo.objects.create(
    nombres="Prueba", apellidos="Horarios", colegiado="COL-TEST-1", especialidad=esp
)
url = reverse("agenda:horarios", args=[nuevo.pk])

print("1. Pantalla de un odontólogo sin horarios")
r = c.get(url)
probar("responde 200", r.status_code == 200, r.status_code)
probar(
    "muestra la advertencia de sin horario",
    "no tiene horario de atención configurado" in r.content.decode(),
)

print("\n2. Agregar una franja")
r = c.post(
    url, {"dia_semana": "LUN", "hora_inicio": "08:00", "hora_fin": "12:00"}, follow=True
)
franjas = HorarioDisponibilidad.objects.filter(odontologo=nuevo, estado=True)
probar("se creó 1 franja", franjas.count() == 1, franjas.count())
probar("mensaje de éxito", "franja de atención registrada" in r.content.decode())
probar(
    "ya no muestra la advertencia",
    "no tiene horario de atención configurado" not in r.content.decode(),
)

print("\n3. Rechazo de franja traslapada")
r = c.post(url, {"dia_semana": "LUN", "hora_inicio": "11:00", "hora_fin": "13:00"})
probar(
    "no se creó",
    HorarioDisponibilidad.objects.filter(odontologo=nuevo, estado=True).count() == 1,
)
probar("explica el traslape", "se traslapa con una ya registrada" in r.content.decode())

print("\n4. Rechazo de hora fin <= hora inicio")
r = c.post(url, {"dia_semana": "MAR", "hora_inicio": "15:00", "hora_fin": "15:00"})
probar(
    "no se creó",
    not HorarioDisponibilidad.objects.filter(
        odontologo=nuevo, dia_semana="MAR", estado=True
    ).exists(),
)
probar("explica el error", "debe ser posterior a la de inicio" in r.content.decode())

print("\n5. Replicar de lunes a viernes")
r = c.post(
    url,
    {
        "dia_semana": "LUN",
        "hora_inicio": "14:00",
        "hora_fin": "18:00",
        "replicar": "on",
    },
    follow=True,
)
tarde = HorarioDisponibilidad.objects.filter(
    odontologo=nuevo, estado=True, hora_inicio="14:00"
)
probar("creó 5 franjas (LUN a VIE)", tarde.count() == 5, tarde.count())
probar(
    "no tocó sábado",
    not HorarioDisponibilidad.objects.filter(
        odontologo=nuevo, dia_semana="SAB", estado=True
    ).exists(),
)

print("\n6. Replicar rechazado si traslapa en cualquier día hábil")
r = c.post(
    url,
    {
        "dia_semana": "MIE",
        "hora_inicio": "15:00",
        "hora_fin": "16:00",
        "replicar": "on",
    },
)
probar(
    "no creó ninguna",
    HorarioDisponibilidad.objects.filter(
        odontologo=nuevo, estado=True, hora_inicio="15:00"
    ).count()
    == 0,
)
probar("explica el traslape", "se traslapa con una ya registrada" in r.content.decode())

print("\n7. Total de horas semanales")
r = c.get(url)
texto = r.content.decode()
# LUN 08-12 (4h) + LUN-VIE 14-18 (20h) = 24 h
probar(
    "reporta 24 horas por semana",
    ("24,0 hora" in texto or "24.0 hora" in texto),
    [l.strip() for l in texto.splitlines() if "por semana" in l],
)

print("\n8. Retirar una franja (borrado lógico)")
franja = HorarioDisponibilidad.objects.get(
    odontologo=nuevo, dia_semana="LUN", hora_inicio="08:00"
)
r = c.post(reverse("agenda:quitar_horario", args=[franja.pk]), follow=True)
franja.refresh_from_db()
probar("la franja quedó inactiva", franja.estado is False)
probar(
    "sigue existiendo el registro (borrado lógico)",
    HorarioDisponibilidad.objects.filter(pk=franja.pk).exists(),
)

print("\n9. Advertencia al retirar una franja con citas futuras")
odo = Odontologo.objects.filter(citas__isnull=False, estado=True).distinct().first()
cita = (
    Cita.objects.filter(odontologo=odo, estado=True)
    .exclude(estado_cita="CANCELADA")
    .filter(fecha__gte=_hoy())
    .order_by("fecha")
    .first()
)
if cita:
    dia = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"][cita.fecha.weekday()]
    contenedora = [
        f
        for f in HorarioDisponibilidad.objects.filter(
            odontologo=odo, dia_semana=dia, estado=True
        )
        if f.hora_inicio <= cita.hora_inicio_programada <= f.hora_fin
    ]
    if contenedora:
        r = c.post(
            reverse("agenda:quitar_horario", args=[contenedora[0].pk]), follow=True
        )
        cuerpo = r.content.decode()
        probar(
            "advierte sobre las citas ya programadas",
            "cita" in cuerpo and ("programada" in cuerpo or "agendada" in cuerpo),
        )
        print(
            "     mensaje:",
            [l.strip() for l in cuerpo.splitlines() if "alert-warning" in l][:1],
        )
    else:
        print("  (omitida: la cita no cae dentro de una franja activa)")
else:
    print("  (omitida: no hay citas futuras sembradas)")

print("\n10. Enlace desde el catálogo de odontólogos")
r = c.get(reverse("catalogo:lista", args=["odontologos"]))
cuerpo = r.content.decode()
probar("el listado responde 200", r.status_code == 200, r.status_code)
probar("incluye el enlace a horarios", f"/horarios/{nuevo.pk}/" in cuerpo)
probar(
    "marca al odontólogo sin franjas",
    "Configurar" in cuerpo or "bi-exclamation-triangle" in cuerpo,
)

print("\n11. La cita ya se puede programar con el odontólogo nuevo")
from pacientes.models import Paciente  # noqa: E402
from catalogo.models import Procedimiento  # noqa: E402
from datetime import timedelta  # noqa: E402
from django.utils import timezone as tz  # noqa: E402

pac = Paciente.objects.filter(estado=True).first()
proc = Procedimiento.objects.filter(estado=True).first()
# Se elige un lunes que la agenda sembrada no haya ocupado: con dos meses de
# citas de demostración las dos unidades dentales quedan tomadas en las fechas
# cercanas, y el rechazo sería por falta de sillón y no por el horario.
prox_lunes = tz.localdate() + timedelta(days=(7 - tz.localdate().weekday()) % 7 or 7)
while Cita.objects.filter(fecha=prox_lunes).exists():
    prox_lunes += timedelta(days=7)
r = c.post(
    reverse("agenda:crear"),
    {
        "paciente": pac.pk,
        "odontologo": nuevo.pk,
        "procedimiento": proc.pk,
        "fecha": prox_lunes.isoformat(),
        "hora_inicio_programada": "15:00",
        "duracion_asignada_min": 30,
        "num_piezas": 1,
        "observaciones": "",
    },
    follow=True,
)
creada = Cita.objects.filter(odontologo=nuevo, fecha=prox_lunes).exists()
probar(
    "la cita se creó dentro de la franja 14:00-18:00",
    creada,
    [l.strip() for l in r.content.decode().splitlines() if "text-danger" in l][:2],
)

print("\n12. Fuera de la franja sigue siendo rechazada")
r = c.post(
    reverse("agenda:crear"),
    {
        "paciente": pac.pk,
        "odontologo": nuevo.pk,
        "procedimiento": proc.pk,
        "fecha": prox_lunes.isoformat(),
        "hora_inicio_programada": "20:00",
        "duracion_asignada_min": 30,
        "num_piezas": 1,
        "observaciones": "",
    },
)
probar(
    "rechaza fuera de horario", "fuera del horario de atención" in r.content.decode()
)

print(f"\n=== {ok} correctas, {fallo} fallidas ===")

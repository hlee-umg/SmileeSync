"""Verifica el expediente clínico: odontograma, notas, planes y cobros."""

import os
from datetime import timedelta
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from agenda.models import Cita  # noqa: E402
from catalogo.models import Odontologo, Procedimiento  # noqa: E402
from clinico.models import (
    DetallePlan,
    Hallazgo,
    NotaClinica,  # noqa: E402
    Pago,
    PlanTratamiento,
    odontograma_vigente,
)
from pacientes.models import Paciente  # noqa: E402
from usuarios.models import Usuario  # noqa: E402

ok = fallo = 0


def probar(titulo, condicion, detalle=""):
    global ok, fallo
    if condicion:
        ok += 1
        print(f"  OK    {titulo}")
    else:
        fallo += 1
        print(f"  FALLA {titulo} {detalle}")


hoy = timezone.localdate()
# Se busca un día hábil que la agenda sembrada no haya ocupado: dos meses
# de citas de demostración dejan sin espacio las fechas cercanas.
futuro = hoy + timedelta(days=1)
while futuro.weekday() > 4 or Cita.objects.filter(fecha=futuro).exists():
    futuro += timedelta(days=1)

admin = Usuario.objects.get(email="admin@smileesync.local")
odo_usuario = Usuario.objects.get(email="hjlee@smileesync.local")
recep = Usuario.objects.get(email="recepcion@smileesync.local")

c_admin, c_odo, c_recep = Client(), Client(), Client()
c_admin.force_login(admin)
c_odo.force_login(odo_usuario)
c_recep.force_login(recep)

paciente = Paciente.objects.get(codigo="PAC-0001")
giron = Odontologo.objects.get(colegiado="CD-20451")

print("1. Quién escribe el expediente y quién cobra")
probar("el administrador escribe el expediente", admin.puede_escribir("clinico"))
probar("el odontólogo escribe el expediente", odo_usuario.puede_escribir("clinico"))
probar(
    "el odontólogo sigue sin escribir la agenda",
    not odo_usuario.puede_escribir("agenda"),
)
probar("la recepción consulta el expediente", recep.puede("clinico"))
probar("la recepción no escribe el expediente", not recep.puede_escribir("clinico"))
probar("la recepción cobra", recep.puede_escribir("finanzas"))
probar("el odontólogo no cobra", not odo_usuario.puede_escribir("finanzas"))

url_odontograma = reverse("clinico:odontograma", args=[paciente.pk])
probar(
    "la recepción abre el odontograma", c_recep.get(url_odontograma).status_code == 200
)
probar(
    "la recepción no puede registrar un hallazgo",
    c_recep.post(
        url_odontograma,
        {"pieza": 15, "cara": "TODA", "tipo": "CARIES", "fecha": hoy.isoformat()},
    ).status_code
    == 403,
)

print("\n2. El odontograma dibuja la arcada completa")
cuerpo = c_odo.get(url_odontograma).content.decode()
probar("responde 200", "Estado actual de la boca" in cuerpo)
probar(
    "dibuja las 32 piezas permanentes",
    cuerpo.count('class="pieza ') == 32,
    cuerpo.count('class="pieza '),
)
probar("marca las piezas patológicas", "pieza-patologica" in cuerpo)
probar("marca las piezas ausentes", "pieza-ausente" in cuerpo)
probar(
    "muestra los cuatro cuadrantes",
    cuerpo.count('class="cuadrante-rotulo"') == 4,
    cuerpo.count('class="cuadrante-rotulo"'),
)

print("\n3. Se registra un hallazgo y el más reciente es el vigente")
antes = Hallazgo.objects.filter(paciente=paciente).count()
r = c_odo.post(
    url_odontograma,
    {
        "pieza": 15,
        "cara": "O",
        "tipo": "CARIES",
        "fecha": hoy.isoformat(),
        "observacion": "Caries oclusal",
    },
    follow=True,
)
probar(
    "el hallazgo se crea",
    Hallazgo.objects.filter(paciente=paciente).count() == antes + 1,
)
probar(
    "queda como vigente de la pieza 15",
    odontograma_vigente(paciente).get(15, {}).get("O").tipo == "CARIES",
)
c_odo.post(
    url_odontograma,
    {
        "pieza": 15,
        "cara": "O",
        "tipo": "OBTURADA",
        "fecha": hoy.isoformat(),
        "observacion": "Resina colocada",
    },
    follow=True,
)
probar(
    "el hallazgo posterior sustituye al anterior en el odontograma",
    odontograma_vigente(paciente).get(15, {}).get("O").tipo == "OBTURADA",
)
probar(
    "el anterior sigue en el historial",
    Hallazgo.objects.filter(
        paciente=paciente, pieza=15, cara="O", tipo="CARIES", estado=True
    ).exists(),
)

print("\n4. Validaciones del odontograma")
r = c_odo.post(
    url_odontograma,
    {"pieza": 14, "cara": "O", "tipo": "AUSENTE", "fecha": hoy.isoformat()},
)
probar("una pieza ausente no se registra por cara", "no una cara" in r.content.decode())
r = c_odo.post(
    url_odontograma,
    {
        "pieza": 14,
        "cara": "TODA",
        "tipo": "CARIES",
        "fecha": (hoy + timedelta(days=3)).isoformat(),
    },
)
probar(
    "no se acepta un hallazgo con fecha futura", "en el futuro" in r.content.decode()
)

print("\n5. Al retirar un hallazgo vuelve a regir el anterior")
ultimo = Hallazgo.objects.filter(
    paciente=paciente, pieza=15, cara="O", tipo="OBTURADA"
).first()
c_odo.post(reverse("clinico:quitar_hallazgo", args=[ultimo.pk]), follow=True)
probar(
    "el vigente vuelve a ser el hallazgo previo",
    odontograma_vigente(paciente).get(15, {}).get("O").tipo == "CARIES",
)

print("\n6. Notas clínicas: validaciones")
url_nota = reverse("clinico:nota_nueva", args=[paciente.pk])
base_nota = {
    "odontologo": giron.pk,
    "fecha": hoy.isoformat(),
    "motivo": "Control",
    "procedimiento_realizado": "Revisión general",
    "num_piezas": 1,
}
r = c_odo.post(url_nota, dict(base_nota, piezas_tratadas="16, 26", num_piezas=1))
probar(
    "el número de piezas debe coincidir con las enumeradas",
    "debe coincidir" in r.content.decode(),
)
r = c_odo.post(url_nota, dict(base_nota, piezas_tratadas="99"))
probar(
    "rechaza una pieza que no existe en la nomenclatura FDI",
    "piezas FDI válidas" in r.content.decode(),
)
r = c_odo.post(url_nota, dict(base_nota, complicacion="on"))
probar(
    "una complicación exige su descripción",
    "Describa la complicación" in r.content.decode(),
)

print("\n7. La nota se liga a la cita atendida")
cita_sin_nota = None
for cita in Cita.objects.filter(estado_cita="ATENDIDA", estado=True):
    if not NotaClinica.objects.filter(cita=cita).exists():
        cita_sin_nota = cita
        break
if cita_sin_nota is None:
    # El seed documenta todas las atendidas, así que se libera una para probar.
    borrar = NotaClinica.objects.filter(cita__isnull=False).first()
    cita_sin_nota = borrar.cita
    borrar.delete()

r = c_admin.get(
    f'{reverse("clinico:nota_nueva", args=[cita_sin_nota.paciente_id])}'
    f"?cita={cita_sin_nota.pk}"
)
cuerpo = r.content.decode()
probar("el formulario avisa de la cita ligada", "Ligada a la cita" in cuerpo)
probar(
    "precarga el procedimiento como motivo",
    cita_sin_nota.procedimiento.nombre in cuerpo,
)
r = c_admin.post(
    f'{reverse("clinico:nota_nueva", args=[cita_sin_nota.paciente_id])}'
    f"?cita={cita_sin_nota.pk}",
    {
        "odontologo": cita_sin_nota.odontologo_id,
        "fecha": cita_sin_nota.fecha.isoformat(),
        "motivo": "Atención programada",
        "procedimiento_realizado": "Concluido sin novedad",
        "piezas_tratadas": "16, 17",
        "num_piezas": 2,
        "anestesia": "on",
    },
    follow=True,
)
nota = NotaClinica.objects.filter(cita=cita_sin_nota).first()
probar("la nota queda ligada a la cita", nota is not None)
probar(
    "guarda las variables que usa el modelo",
    nota and nota.num_piezas == 2 and nota.anestesia is True,
    nota and (nota.num_piezas, nota.anestesia),
)
r = c_admin.get(
    f'{reverse("clinico:nota_nueva", args=[cita_sin_nota.paciente_id])}'
    f"?cita={cita_sin_nota.pk}",
    follow=True,
)
probar(
    "no se documenta dos veces la misma cita", "ya tiene una nota" in r.content.decode()
)

print("\n8. Plan de tratamiento: creación y renglones")
r = c_odo.post(
    reverse("clinico:plan_nuevo", args=[paciente.pk]),
    {
        "odontologo": giron.pk,
        "fecha": hoy.isoformat(),
        "diagnostico": "Dos caries oclusales y profilaxis previa requerida.",
        "descuento": "0",
    },
    follow=True,
)
plan = PlanTratamiento.objects.filter(paciente=paciente).order_by("-id").first()
probar("el plan se crea en borrador", plan.estado_plan == "BORRADOR")
probar("recibe un código de la serie", plan.codigo.startswith("PLAN-"), plan.codigo)

url_plan = reverse("clinico:plan_detalle", args=[plan.pk])
r = c_odo.post(
    reverse("clinico:plan_estado", args=[plan.pk]),
    {"estado_plan": "APROBADO"},
    follow=True,
)
plan.refresh_from_db()
probar("no se aprueba un plan sin renglones", plan.estado_plan == "BORRADOR")
probar("el mensaje lo explica", "al menos un renglón" in r.content.decode())

profilaxis = Procedimiento.objects.get(codigo="PROC-001")
resina = Procedimiento.objects.get(codigo="PROC-002")
conducto = Procedimiento.objects.get(codigo="PROC-003")

c_odo.post(
    url_plan,
    {"accion": "renglon", "fase": 1, "procedimiento": profilaxis.pk, "num_piezas": 1},
    follow=True,
)
renglon = DetallePlan.objects.filter(plan=plan).order_by("-id").first()
probar(
    "el renglón toma el precio de lista del catálogo",
    renglon.precio_unitario == profilaxis.precio,
    f"{renglon.precio_unitario} vs {profilaxis.precio}",
)
probar(
    "el modelo le estima una duración",
    renglon.duracion_estimada_min > 0,
    renglon.duracion_estimada_min,
)
probar(
    "registra el origen de la estimación",
    renglon.origen_estimacion in ("modelo", "historico", "catalogo"),
    renglon.origen_estimacion,
)

for pieza in (16, 26):
    c_odo.post(
        url_plan,
        {
            "accion": "renglon",
            "fase": 2,
            "procedimiento": resina.pk,
            "pieza": pieza,
            "num_piezas": 1,
        },
        follow=True,
    )
c_odo.post(
    url_plan,
    {
        "accion": "renglon",
        "fase": 2,
        "procedimiento": conducto.pk,
        "pieza": 46,
        "num_piezas": 1,
    },
    follow=True,
)
plan.refresh_from_db()
probar(
    "el plan acumula cuatro renglones", plan.total_renglones == 4, plan.total_renglones
)
probar(
    "el total es la suma de los importes",
    plan.total == sum(d.importe for d in plan.renglones),
    plan.total,
)

print("\n9. Los renglones se reparten en sesiones de sillón")
sesiones = plan.sesiones_sugeridas()
probar("propone más de una sesión", len(sesiones) > 1, len(sesiones))
probar(
    "ninguna sesión pasa de 120 minutos",
    all(s["minutos"] <= 120 for s in sesiones),
    [s["minutos"] for s in sesiones],
)
probar(
    "ninguna sesión mezcla fases",
    all(len({d.fase for d in s["renglones"]}) == 1 for s in sesiones),
)
probar("la primera sesión es la de la fase 1", sesiones[0]["fase"] == 1)
probar(
    "los minutos estimados del plan son la suma de sus renglones",
    plan.minutos_estimados == sum(d.duracion_estimada_min for d in plan.renglones),
)

print("\n10. Aprobación y agendado de un renglón")
c_odo.post(
    reverse("clinico:plan_estado", args=[plan.pk]),
    {"estado_plan": "APROBADO"},
    follow=True,
)
plan.refresh_from_db()
probar("el plan queda aprobado", plan.estado_plan == "APROBADO")
probar("registra la fecha de aprobación", plan.fecha_aprobacion == hoy)

primero = plan.renglones.order_by("fase", "orden").first()
url_agendar = reverse("clinico:agendar_renglon", args=[primero.pk])
probar(
    "el odontólogo no agenda (no escribe la agenda)",
    c_odo.get(url_agendar).status_code == 403,
)
r = c_recep.get(url_agendar)
probar("la recepción sí agenda", r.status_code == 302, r.status_code)
probar(
    "el destino es el formulario de cita con los datos del renglón",
    f"renglon={primero.pk}" in r.url and f"paciente={paciente.pk}" in r.url,
    r.url,
)
cuerpo = c_recep.get(r.url).content.decode()
probar("el formulario avisa de qué renglón viene", "atiende el renglón" in cuerpo)
probar(
    "precarga la duración estimada del plan",
    f'value="{primero.duracion_estimada_min}"' in cuerpo,
)

hora_elegida = None
for hora in ("14:00", "14:30", "15:00", "15:30", "16:00", "16:30"):
    antes = Cita.objects.count()
    r = c_recep.post(
        reverse("agenda:crear"),
        {
            "paciente": paciente.pk,
            "odontologo": giron.pk,
            "procedimiento": primero.procedimiento_id,
            "fecha": futuro.isoformat(),
            "hora_inicio_programada": hora,
            "duracion_asignada_min": primero.duracion_estimada_min,
            "num_piezas": 1,
            "observaciones": "",
            "renglon": primero.pk,
        },
        follow=True,
    )
    if Cita.objects.count() == antes + 1:
        hora_elegida = hora
        break
probar("la cita del renglón se programa", hora_elegida is not None)
primero.refresh_from_db()
probar(
    "el renglón queda agendado",
    primero.estado_detalle == "AGENDADO",
    primero.estado_detalle,
)
probar("el renglón apunta a la cita", primero.cita is not None)

print("\n11. Al registrar la atención el renglón se cierra y el plan avanza")
cita_plan = primero.cita
r = c_recep.post(
    reverse("agenda:tiempos", args=[cita_plan.pk]),
    {"hora_inicio_real": hora_elegida, "hora_fin_real": "16:55"},
    follow=True,
)
primero.refresh_from_db()
plan.refresh_from_db()
probar(
    "el renglón queda completado",
    primero.estado_detalle == "COMPLETADO",
    primero.estado_detalle,
)
probar("el plan pasa a en curso", plan.estado_plan == "EN_CURSO", plan.estado_plan)
probar("el avance refleja un renglón de cuatro", plan.avance == 25, plan.avance)
probar(
    "los minutos pendientes bajan",
    plan.minutos_pendientes < plan.minutos_estimados,
    f"{plan.minutos_pendientes} / {plan.minutos_estimados}",
)
probar("el aviso del plan aparece al cerrar la cita", plan.codigo in r.content.decode())

print("\n12. Cobros: abonos, saldo y anulación")
probar("el plan nace con el saldo completo", plan.saldo == plan.total, plan.saldo)
r = c_odo.post(
    url_plan,
    {
        "accion": "pago",
        "fecha": hoy.isoformat(),
        "monto": "100.00",
        "metodo": "EFECTIVO",
    },
)
probar("el odontólogo no registra abonos", r.status_code == 403, r.status_code)

total = plan.total
r = c_recep.post(
    url_plan,
    {
        "accion": "pago",
        "fecha": hoy.isoformat(),
        "monto": "200.00",
        "metodo": "EFECTIVO",
        "referencia": "REC-TEST",
    },
    follow=True,
)
plan.refresh_from_db()
probar("el abono se registra", plan.pagado == Decimal("200.00"), plan.pagado)
probar("el saldo baja", plan.saldo == total - Decimal("200.00"), plan.saldo)

r = c_recep.post(
    url_plan,
    {
        "accion": "pago",
        "fecha": hoy.isoformat(),
        "monto": str(total),
        "metodo": "TARJETA",
    },
)
probar("no se puede abonar más que el saldo", "excede el saldo" in r.content.decode())
r = c_recep.post(
    url_plan,
    {
        "accion": "pago",
        "fecha": (hoy + timedelta(days=2)).isoformat(),
        "monto": "50.00",
        "metodo": "EFECTIVO",
    },
)
probar("no se acepta un abono con fecha futura", "fecha futura" in r.content.decode())

pago = Pago.objects.filter(plan=plan, referencia="REC-TEST").first()
c_recep.post(reverse("clinico:anular_pago", args=[pago.pk]), follow=True)
plan.refresh_from_db()
probar("al anular el abono el saldo vuelve", plan.saldo == total, plan.saldo)
probar(
    "el abono anulado se conserva",
    Pago.objects.filter(pk=pago.pk, estado=False).exists(),
)

print("\n13. Pantalla de cobros")
r = c_recep.get(reverse("clinico:cobros"))
cuerpo = r.content.decode()
probar("responde 200", r.status_code == 200, r.status_code)
probar("lista el plan con saldo", plan.codigo in cuerpo)
probar("muestra el total por cobrar", "Por cobrar" in cuerpo)
probar(
    "el odontólogo no entra a cobros",
    c_odo.get(reverse("clinico:cobros")).status_code == 403,
)

print("\n14. El expediente reúne todo en una pantalla")
r = c_odo.get(reverse("clinico:expediente", args=[paciente.pk]))
cuerpo = r.content.decode()
probar("responde 200", r.status_code == 200, r.status_code)
probar("muestra el plan", plan.codigo in cuerpo)
probar("muestra el resumen del odontograma", "Hallazgos por atender" in cuerpo)
probar("muestra las visitas documentadas", "Últimas visitas" in cuerpo)
probar("muestra el saldo de tratamientos", "Saldo de tratamientos" in cuerpo)

r = c_odo.get(reverse("clinico:lista"))
probar("el listado de expedientes responde", r.status_code == 200)
probar("cuenta los tratamientos del paciente", paciente.apellidos in r.content.decode())

r = c_recep.get(reverse("clinico:planes"))
probar("el listado de tratamientos responde", r.status_code == 200)
probar(
    "reporta los minutos comprometidos",
    "minutos de sillón comprometidos" in r.content.decode(),
)

print("\n15. El renglón anulado deja de contar")
pendiente = plan.renglones.filter(estado_detalle="PENDIENTE").first()
subtotal_antes = plan.subtotal
c_odo.post(reverse("clinico:quitar_renglon", args=[pendiente.pk]), follow=True)
plan.refresh_from_db()
probar(
    "el subtotal baja al anular el renglón",
    plan.subtotal < subtotal_antes,
    f"{plan.subtotal} / {subtotal_antes}",
)
probar(
    "el renglón anulado no se elimina",
    DetallePlan.objects.filter(pk=pendiente.pk, estado_detalle="ANULADO").exists(),
)
completado = plan.detalles.filter(estado_detalle="COMPLETADO").first()
r = c_odo.post(reverse("clinico:quitar_renglon", args=[completado.pk]), follow=True)
probar(
    "un renglón ya atendido no se puede anular",
    "no puede anularse" in r.content.decode(),
)

print(f"\n=== {ok} correctas, {fallo} fallidas ===")

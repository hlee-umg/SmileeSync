"""Módulo Principal y módulo de Agenda y Citas.

La vista `principal` es la pantalla de inicio del sistema: presenta los
indicadores operativos del día y el calendario semanal de la clínica.
"""

from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from catalogo.models import Odontologo
from inteligencia.servicio import (
    estimar_duracion,
    registrar_dato_entrenamiento,
    registrar_prediccion,
)
from pacientes.models import Paciente
from usuarios.decorators import (
    escritura_requerida,
    modulo_requerido,
    puede_gestionar_odontologo,
)

from .disponibilidad import (
    capacidad_minutos,
    franjas_efectivas,
    hay_traslape,
    unidades_libres,
)
from .forms import AusenciaForm, CitaForm, HorarioForm, RegistrarTiemposForm
from .models import AusenciaOdontologo, Cita, HistorialCita, HorarioDisponibilidad

DIAS = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
NOMBRES_DIA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
HORA_APERTURA = 7
HORA_CIERRE = 19

CLASES_ESTADO = {
    "PROGRAMADA": "cita-prog",
    "ATENDIDA": "cita-aten",
    "CANCELADA": "cita-canc",
    "REPROGRAMADA": "cita-reprog",
}


# ══════════════════════════════ utilidades ══════════════════════════════
def _lunes_de(fecha):
    return fecha - timedelta(days=fecha.weekday())


def _semana_solicitada(request):
    """Lee la semana del parámetro ?semana=AAAA-MM-DD; por omisión, la actual."""
    texto = request.GET.get("semana")
    if texto:
        try:
            return _lunes_de(datetime.strptime(texto, "%Y-%m-%d").date())
        except ValueError:
            pass
    return _lunes_de(timezone.localdate())


def _fecha_solicitada(request, parametro="fecha"):
    """Lee una fecha de la consulta; por omisión, la de hoy."""
    texto = request.GET.get(parametro)
    if texto:
        try:
            return datetime.strptime(texto, "%Y-%m-%d").date()
        except ValueError:
            pass
    return timezone.localdate()


PASO_SUGERENCIA_MIN = 15


def _huecos_sugeridos(odontologo, fechas, duracion, hoy, ahora):
    """Primer inicio viable de cada hora para una cita de `duracion` minutos.

    Un inicio es viable si la cita completa cabe dentro de una franja de
    disponibilidad del odontólogo y no se traslapa con ninguna de sus citas
    vigentes. Devuelve {(indice_dia, hora): 'HH:MM'} para que la plantilla
    resalte esas casillas.
    """
    if not (odontologo and duracion):
        return {}

    ocupadas = {}
    for c in Cita.objects.filter(
        odontologo=odontologo, fecha__in=fechas, estado=True
    ).exclude(estado_cita="CANCELADA"):
        ocupadas.setdefault(c.fecha, []).append(
            (c.hora_inicio_programada, c.hora_fin_programada)
        )

    sugeridos = {}
    for indice, fecha in enumerate(fechas):
        # Disponibilidad efectiva: el patrón semanal menos las ausencias.
        for f_ini, f_fin in franjas_efectivas(odontologo, fecha):
            candidato = datetime.combine(fecha, f_ini)
            limite = datetime.combine(fecha, f_fin)
            while candidato + timedelta(minutes=duracion) <= limite:
                inicio_h = candidato.time()
                fin_h = (candidato + timedelta(minutes=duracion)).time()
                clave = (indice, inicio_h.hour)
                ya_paso = fecha < hoy or (fecha == hoy and inicio_h < ahora)
                choca = any(
                    hay_traslape(inicio_h, fin_h, oi, of)
                    for oi, of in ocupadas.get(fecha, [])
                )
                # Un espacio solo sirve si además queda un sillón libre.
                if not ya_paso and not choca and clave not in sugeridos:
                    if unidades_libres(fecha, inicio_h, fin_h):
                        sugeridos[clave] = inicio_h.strftime("%H:%M")
                candidato += timedelta(minutes=PASO_SUGERENCIA_MIN)
    return sugeridos


def _rejilla(citas, inicio, dias_visibles, sugeridos=None):
    """Organiza las citas en una rejilla de horas por días para la plantilla.

    Cada casilla lleva su fecha y su hora, de modo que la plantilla pueda
    enlazar directamente a la programación de una cita en ese espacio.
    """
    rejilla = {}
    for cita in citas:
        indice_dia = (cita.fecha - inicio).days
        if 0 <= indice_dia < dias_visibles:
            hora = cita.hora_inicio_programada.hour
            rejilla.setdefault(hora, {}).setdefault(indice_dia, []).append(cita)

    # El rango de horas visible abarca tanto las citas existentes como los
    # espacios sugeridos: de lo contrario una recomendación podría quedar
    # fuera de la rejilla y el usuario no la vería.
    horas = sorted(rejilla.keys()) + [h for _, h in (sugeridos or {})]
    if horas:
        desde = max(HORA_APERTURA, min(horas) - 1)
        hasta = min(HORA_CIERRE, max(horas) + 2)
    else:
        desde, hasta = 8, 18

    filas = []
    for hora in range(desde, hasta):
        celdas = []
        for d in range(dias_visibles):
            fecha = inicio + timedelta(days=d)
            celdas.append(
                {
                    "indice": d,
                    "citas": rejilla.get(hora, {}).get(d, []),
                    "fecha": fecha.isoformat(),
                    "hora": f"{hora:02d}:00",
                    "sugerida": (sugeridos or {}).get((d, hora)),
                }
            )
        filas.append({"hora": f"{hora:02d}:00", "celdas": celdas})
    return filas


# ══════════════════════════ MÓDULO PRINCIPAL ══════════════════════════
@login_required
@modulo_requerido("agenda")
def principal(request):
    """Pantalla de inicio: indicadores y calendario, por semana o por día."""
    hoy = timezone.localdate()
    vista = "dia" if request.GET.get("vista") == "dia" else "semana"

    if vista == "dia":
        inicio = _fecha_solicitada(request)
        dias_visibles = 1
        anterior = inicio - timedelta(days=1)
        siguiente = inicio + timedelta(days=1)
        es_periodo_actual = inicio == hoy
    else:
        inicio = _lunes_de(_fecha_solicitada(request, "semana"))
        dias_visibles = 6
        anterior = inicio - timedelta(days=7)
        siguiente = inicio + timedelta(days=7)
        es_periodo_actual = inicio == _lunes_de(hoy)
    fin = inicio + timedelta(days=dias_visibles - 1)
    fechas = [inicio + timedelta(days=i) for i in range(dias_visibles)]

    odontologos = Odontologo.objects.filter(estado=True)

    # Un odontólogo ve su propia agenda al entrar: si no se pidió un filtro
    # explícito y su usuario está vinculado a una ficha, se preselecciona. Que
    # el parámetro no venga significa que es la primera visita; que venga vacío
    # significa que eligió "Todos los odontólogos" a propósito.
    filtro_odontologo = request.GET.get("odontologo")
    ficha_propia = odontologos.filter(usuario=request.user).first()
    if filtro_odontologo is None and ficha_propia:
        filtro_odontologo = str(ficha_propia.pk)
    filtro_odontologo = filtro_odontologo or ""

    citas = (
        Cita.objects.filter(fecha__range=(inicio, fin), estado=True)
        .select_related("paciente", "odontologo", "procedimiento")
        .order_by("fecha", "hora_inicio_programada")
    )
    if filtro_odontologo.isdigit():
        citas = citas.filter(odontologo_id=int(filtro_odontologo))
        odontologos_kpi = odontologos.filter(id=int(filtro_odontologo))
    else:
        odontologos_kpi = odontologos

    for cita in citas:
        cita.clase_css = CLASES_ESTADO.get(cita.estado_cita, "cita-prog")

    # --- recomendación de bloques: dónde cabe el procedimiento elegido ---
    from catalogo.models import Procedimiento

    procedimientos = Procedimiento.objects.filter(estado=True)
    id_proc = request.GET.get("procedimiento", "")
    piezas = request.GET.get("piezas", "1")
    piezas = int(piezas) if piezas.isdigit() and int(piezas) > 0 else 1
    estimacion = None
    sugeridos = {}
    odontologo_sug = (
        odontologos.filter(id=int(filtro_odontologo)).first()
        if filtro_odontologo.isdigit()
        else None
    )
    procedimiento_sug = (
        procedimientos.filter(pk=int(id_proc)).first() if id_proc.isdigit() else None
    )
    if procedimiento_sug and odontologo_sug:
        estimacion = estimar_duracion(
            procedimiento_sug, odontologo_sug, inicio, time(9, 0), piezas
        )
        sugeridos = _huecos_sugeridos(
            odontologo_sug,
            fechas,
            estimacion.duracion_min,
            hoy,
            timezone.localtime().time(),
        )

    # --- indicadores ---
    citas_hoy = sum(1 for c in citas if c.fecha == hoy and c.estado_cita != "CANCELADA")
    minutos_ocupados = (
        citas.exclude(estado_cita="CANCELADA").aggregate(
            total=Sum("duracion_asignada_min")
        )["total"]
        or 0
    )
    minutos_disponibles = capacidad_minutos(list(odontologos_kpi), fechas)
    utilizacion = (
        round(minutos_ocupados / minutos_disponibles * 100)
        if minutos_disponibles
        else 0
    )

    desviacion = Cita.objects.filter(
        estado_cita="ATENDIDA", duracion_real_min__isnull=False, estado=True
    ).aggregate(
        promedio_real=Avg("duracion_real_min"),
        promedio_asignado=Avg("duracion_asignada_min"),
        total=Count("id"),
    )
    if desviacion["total"]:
        error_medio = round(
            abs(
                (desviacion["promedio_real"] or 0)
                - (desviacion["promedio_asignado"] or 0)
            ),
            1,
        )
    else:
        error_medio = None

    contexto = {
        "vista": vista,
        "inicio": inicio,
        "fin": fin,
        "parametro_periodo": "fecha" if vista == "dia" else "semana",
        "periodo_anterior": anterior.isoformat(),
        "periodo_siguiente": siguiente.isoformat(),
        "periodo_hoy": (hoy if vista == "dia" else _lunes_de(hoy)).isoformat(),
        "es_periodo_actual": es_periodo_actual,
        "dias": [
            {"nombre": NOMBRES_DIA[f.weekday()], "fecha": f, "es_hoy": f == hoy}
            for f in fechas
        ],
        "filas": _rejilla(citas, inicio, dias_visibles, sugeridos),
        "procedimientos": procedimientos,
        "procedimiento_sug": id_proc,
        "piezas": piezas,
        "estimacion": estimacion,
        "odontologo_sug": odontologo_sug,
        "ficha_propia": ficha_propia,
        "total_sugeridos": len(sugeridos),
        "odontologos": odontologos,
        "filtro_odontologo": filtro_odontologo,
        "kpi_citas_hoy": citas_hoy,
        "kpi_utilizacion": utilizacion,
        "kpi_pacientes": Paciente.objects.filter(estado=True).count(),
        "kpi_error_medio": error_medio,
        "kpi_citas_periodo": citas.exclude(estado_cita="CANCELADA").count(),
    }
    return render(request, "agenda/principal.html", contexto)


# ══════════════════════════ AGENDA Y CITAS ══════════════════════════
@login_required
@modulo_requerido("agenda")
def lista(request):
    """Consulta de citas por rango de fechas, odontólogo y estado."""
    hoy = timezone.localdate()
    desde = request.GET.get("desde") or _lunes_de(hoy).isoformat()
    hasta = request.GET.get("hasta") or (_lunes_de(hoy) + timedelta(days=6)).isoformat()
    odontologo = request.GET.get("odontologo", "")
    estado_cita = request.GET.get("estado_cita", "")

    citas = (
        Cita.objects.filter(estado=True)
        .select_related("paciente", "odontologo", "procedimiento")
        .order_by("-fecha", "hora_inicio_programada")
    )
    try:
        citas = citas.filter(fecha__range=(desde, hasta))
    except (ValueError, TypeError):
        pass
    if odontologo.isdigit():
        citas = citas.filter(odontologo_id=int(odontologo))
    if estado_cita:
        citas = citas.filter(estado_cita=estado_cita)

    for cita in citas:
        if cita.duracion_real_min:
            cita.desvio = cita.duracion_real_min - cita.duracion_asignada_min
        else:
            cita.desvio = None

    return render(
        request,
        "agenda/lista.html",
        {
            "citas": citas[:200],
            "desde": desde,
            "hasta": hasta,
            "odontologo": odontologo,
            "estado_cita": estado_cita,
            "odontologos": Odontologo.objects.filter(estado=True),
            "estados": Cita.ESTADOS,
        },
    )


@login_required
@modulo_requerido("agenda")
def detalle(request, pk):
    """Ficha de una cita, con las acciones disponibles según su estado.

    Es el destino al pulsar una cita en el calendario: reúne en un solo lugar
    la reprogramación, el registro de la atención y la cancelación, que antes
    estaban repartidas entre el listado y la propia rejilla.
    """
    cita = get_object_or_404(
        Cita.objects.select_related("paciente", "odontologo", "procedimiento"), pk=pk
    )

    prediccion = cita.predicciones.select_related("modelo").order_by("-fecha").first()
    abierta = cita.estado_cita in ("PROGRAMADA", "REPROGRAMADA")
    desvio = None
    if cita.duracion_real_min:
        desvio = cita.duracion_real_min - cita.duracion_asignada_min

    return render(
        request,
        "agenda/detalle.html",
        {
            "cita": cita,
            "prediccion": prediccion,
            "abierta": abierta,
            "desvio": desvio,
            # Enlaces al expediente: la nota de la visita y el renglón del plan de
            # tratamiento que esta cita atiende, si viene de uno.
            "nota": cita.nota if _tiene_nota(cita) else None,
            "renglones": cita.renglones_plan.filter(estado=True).select_related(
                "plan", "procedimiento"
            ),
            "volver": request.GET.get("volver") or reverse("agenda:principal"),
        },
    )


def _estimacion_para(form):
    """Calcula la estimación de duración con los datos que ya tiene el formulario."""
    datos = form.data if form.is_bound else {}
    try:
        from catalogo.models import Odontologo as Odo, Procedimiento as Proc

        id_proc = (datos.get("procedimiento") or "").strip()
        id_odo = (datos.get("odontologo") or "").strip()
        if not (id_proc.isdigit() and id_odo.isdigit()):
            return None
        procedimiento = Proc.objects.filter(pk=int(id_proc)).first()
        odontologo = Odo.objects.filter(pk=int(id_odo)).first()
        if not (procedimiento and odontologo):
            return None
        fecha = datetime.strptime(datos.get("fecha"), "%Y-%m-%d").date()
        hora = datetime.strptime(datos.get("hora_inicio_programada"), "%H:%M").time()
        piezas = int(datos.get("num_piezas") or 1)
    except (ValueError, TypeError):
        return None
    return estimar_duracion(procedimiento, odontologo, fecha, hora, piezas)


@login_required
@modulo_requerido("agenda")
def estimar(request):
    """Devuelve la estimación de duración en formato JSON.

    La consulta el formulario de cita cada vez que cambian el procedimiento, el
    odontólogo, la fecha, la hora o el número de piezas, de modo que el usuario
    vea la recomendación antes de decidir la duración.
    """
    from django.http import JsonResponse
    from catalogo.models import Odontologo as Odo, Procedimiento as Proc

    id_proc = (request.GET.get("procedimiento") or "").strip()
    id_odo = (request.GET.get("odontologo") or "").strip()
    if not (id_proc.isdigit() and id_odo.isdigit()):
        return JsonResponse({"disponible": False})

    procedimiento = Proc.objects.filter(pk=int(id_proc), estado=True).first()
    odontologo = Odo.objects.filter(pk=int(id_odo), estado=True).first()
    if not (procedimiento and odontologo):
        return JsonResponse({"disponible": False})

    try:
        fecha = datetime.strptime(request.GET.get("fecha"), "%Y-%m-%d").date()
        hora = datetime.strptime(request.GET.get("hora"), "%H:%M").time()
    except (ValueError, TypeError):
        fecha, hora = timezone.localdate(), time(9, 0)

    piezas = int(request.GET.get("piezas") or 1)
    est = estimar_duracion(procedimiento, odontologo, fecha, hora, piezas)
    return JsonResponse(
        {
            "disponible": True,
            "duracion": est.duracion_min,
            "bloque_min": est.bloque_min,
            "bloque_max": est.bloque_max,
            "origen": est.origen,
            "etiqueta_origen": est.etiqueta_origen,
            "detalle": est.detalle,
        }
    )


def _renglon_solicitado(request):
    """Renglón del plan de tratamiento que esta cita va a atender, si viene uno.

    Es el vínculo entre el plan y la agenda: el plan presupuesta el trabajo y la
    cita lo ejecuta, de modo que al programarla el renglón queda marcado como
    agendado en lugar de quedar suelto.
    """
    from clinico.models import DetallePlan, PlanTratamiento

    valor = request.POST.get("renglon") or request.GET.get("renglon") or ""
    if not valor.isdigit():
        return None
    return (
        DetallePlan.objects.filter(
            pk=int(valor),
            estado=True,
            estado_detalle="PENDIENTE",
            plan__estado_plan__in=PlanTratamiento.ABIERTOS,
        )
        .select_related("plan")
        .first()
    )


@login_required
@escritura_requerida("agenda")
def crear(request):
    estimacion = None
    renglon = _renglon_solicitado(request)
    if request.method == "POST":
        form = CitaForm(request.POST)
        estimacion = _estimacion_para(form)
        if form.is_valid():
            cita = form.save()
            if estimacion:
                registrar_prediccion(cita, estimacion)
            HistorialCita.objects.create(
                cita_ref=cita.pk,
                paciente=str(cita.paciente),
                odontologo=str(cita.odontologo),
                fecha_cita=cita.fecha,
                estado_cita_anterior="",
                accion="CREACION",
                realizado_por=request.user.username,
            )
            messages.success(
                request,
                f"Cita programada para {cita.paciente} "
                f'el {cita.fecha.strftime("%d/%m/%Y")} '
                f'a las {cita.hora_inicio_programada.strftime("%H:%M")}.',
            )
            if renglon and renglon.plan.paciente_id == cita.paciente_id:
                renglon.cita = cita
                renglon.estado_detalle = "AGENDADO"
                renglon.save(update_fields=["cita", "estado_detalle"])
                messages.info(
                    request,
                    f"Queda ligada al renglón «{renglon}» del "
                    f"plan {renglon.plan.codigo}.",
                )
                return redirect("clinico:plan_detalle", pk=renglon.plan_id)
            return redirect("agenda:principal")
    else:
        inicial = {}
        if request.GET.get("fecha"):
            inicial["fecha"] = request.GET["fecha"]
        if request.GET.get("hora"):
            inicial["hora_inicio_programada"] = request.GET["hora"]
        # Al programar desde una casilla del calendario, el odontólogo del
        # filtro activo viene preseleccionado.
        if request.GET.get("odontologo", "").isdigit():
            inicial["odontologo"] = int(request.GET["odontologo"])
        if request.GET.get("procedimiento", "").isdigit():
            inicial["procedimiento"] = int(request.GET["procedimiento"])
        # Al venir de un plan de tratamiento, llegan además el paciente y la
        # duración que el modelo estimó al presupuestar el renglón.
        if request.GET.get("paciente", "").isdigit():
            inicial["paciente"] = int(request.GET["paciente"])
        if request.GET.get("duracion", "").isdigit():
            inicial["duracion_asignada_min"] = int(request.GET["duracion"])
        if request.GET.get("piezas", "").isdigit():
            inicial["num_piezas"] = int(request.GET["piezas"])
        form = CitaForm(initial=inicial)

    return render(
        request,
        "agenda/form.html",
        {
            "form": form,
            "titulo": "Programar nueva cita",
            "estimacion": estimacion,
            "es_nueva": True,
            "renglon": renglon,
        },
    )


@login_required
@escritura_requerida("agenda")
def editar(request, pk):
    """Reprogramación de una cita existente."""
    cita = get_object_or_404(Cita, pk=pk, estado=True)
    if request.method == "POST":
        form = CitaForm(request.POST, instance=cita)
        estimacion = _estimacion_para(form)
        if form.is_valid():
            HistorialCita.objects.create(
                cita_ref=cita.pk,
                paciente=str(cita.paciente),
                odontologo=str(cita.odontologo),
                fecha_cita=cita.fecha,
                estado_cita_anterior=cita.estado_cita,
                accion="REPROGRAMACION",
                realizado_por=request.user.username,
            )
            cita = form.save()
            if cita.estado_cita == "PROGRAMADA":
                cita.estado_cita = "REPROGRAMADA"
                cita.save(update_fields=["estado_cita"])
            messages.success(request, "La cita fue reprogramada correctamente.")
            return redirect("agenda:principal")
    else:
        form = CitaForm(instance=cita)
        estimacion = estimar_duracion(
            cita.procedimiento, cita.odontologo, cita.fecha, cita.hora_inicio_programada
        )

    return render(
        request,
        "agenda/form.html",
        {
            "form": form,
            "titulo": f"Reprogramar cita de {cita.paciente}",
            "estimacion": estimacion,
            "cita": cita,
            "es_nueva": False,
        },
    )


@login_required
@escritura_requerida("agenda")
def cancelar(request, pk):
    """Cancelación de una cita: cambia su estado y conserva el registro."""
    cita = get_object_or_404(Cita, pk=pk, estado=True)
    if request.method == "POST":
        HistorialCita.objects.create(
            cita_ref=cita.pk,
            paciente=str(cita.paciente),
            odontologo=str(cita.odontologo),
            fecha_cita=cita.fecha,
            estado_cita_anterior=cita.estado_cita,
            accion="CANCELACION",
            realizado_por=request.user.username,
        )
        motivo = request.POST.get("motivo", "").strip()
        cita.estado_cita = "CANCELADA"
        if motivo:
            cita.observaciones = (
                cita.observaciones + f"\nCancelación: {motivo}"
            ).strip()
        cita.save(update_fields=["estado_cita", "observaciones"])
        messages.success(request, f"La cita de {cita.paciente} fue cancelada.")
    # Solo se vuelve a una dirección del propio sitio: aceptar cualquier URL
    # permitiría usar la cancelación para redirigir a un sitio externo.
    siguiente = request.POST.get("siguiente")
    if siguiente and url_has_allowed_host_and_scheme(
        siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(siguiente)
    return redirect("agenda:principal")


@login_required
@escritura_requerida("agenda")
def horarios(request, odontologo_id):
    """Configuración de las franjas de atención de un odontólogo.

    Sin franjas registradas el sistema rechaza todas sus citas, por lo que esta
    pantalla es el paso obligatorio tras dar de alta a un profesional.
    """
    odontologo = get_object_or_404(Odontologo, pk=odontologo_id)

    if request.method == "POST":
        form = HorarioForm(request.POST, odontologo=odontologo)
        if form.is_valid():
            creadas = form.guardar()
            if creadas:
                messages.success(
                    request,
                    f'{len(creadas)} franja{"s" if len(creadas) != 1 else ""} '
                    f'de atención registrada{"s" if len(creadas) != 1 else ""} '
                    f"para {odontologo}.",
                )
            else:
                messages.info(request, "Esa franja ya estaba registrada.")
            return redirect("agenda:horarios", odontologo_id=odontologo.pk)
    else:
        form = HorarioForm(odontologo=odontologo)

    # Franjas agrupadas por día, para presentarlas como una semana
    franjas = HorarioDisponibilidad.objects.filter(
        odontologo=odontologo, estado=True
    ).order_by("hora_inicio")
    etiquetas = dict(HorarioDisponibilidad.DIAS)
    semana = []
    for codigo in DIAS[:6]:
        del_dia = [f for f in franjas if f.dia_semana == codigo]
        minutos = sum(
            (
                datetime.combine(date.today(), f.hora_fin)
                - datetime.combine(date.today(), f.hora_inicio)
            ).seconds
            // 60
            for f in del_dia
        )
        semana.append(
            {
                "codigo": codigo,
                "nombre": etiquetas.get(codigo, codigo),
                "franjas": del_dia,
                "horas": round(minutos / 60, 1),
            }
        )

    return render(
        request,
        "agenda/horarios.html",
        {
            "odontologo": odontologo,
            "semana": semana,
            "form": form,
            "total_franjas": franjas.count(),
            "horas_semana": round(sum(d["horas"] for d in semana), 1),
        },
    )


@login_required
@escritura_requerida("agenda")
def quitar_horario(request, pk):
    """Retira una franja de disponibilidad mediante borrado lógico.

    Si la franja tiene citas futuras dentro de ella, se informa al usuario:
    las citas ya programadas se conservan, pero no podrán reprogramarse en ese
    rango mientras la franja siga retirada.
    """
    franja = get_object_or_404(HorarioDisponibilidad, pk=pk)
    odontologo_id = franja.odontologo.pk

    if request.method == "POST":
        indice_dia = (
            DIAS.index(franja.dia_semana) if franja.dia_semana in DIAS else None
        )
        afectadas = 0
        if indice_dia is not None:
            afectadas = (
                Cita.objects.filter(
                    odontologo=franja.odontologo,
                    fecha__gte=timezone.localdate(),
                    hora_inicio_programada__gte=franja.hora_inicio,
                    hora_fin_programada__lte=franja.hora_fin,
                    estado=True,
                )
                .exclude(estado_cita="CANCELADA")
                .count()
            )

        franja.estado = False
        franja.save(update_fields=["estado"])

        if afectadas:
            messages.warning(
                request,
                f"Franja retirada. Atención: hay {afectadas} cita"
                f'{"s" if afectadas != 1 else ""} futura'
                f'{"s" if afectadas != 1 else ""} dentro de ese horario; '
                f"se conservan, pero no podrán reprogramarse en ese rango.",
            )
        else:
            messages.success(request, "Franja de atención retirada.")

    return redirect("agenda:horarios", odontologo_id=odontologo_id)


def _tiene_nota(cita):
    """Si la cita ya tiene nota clínica. El acceso inverso uno a uno levanta
    excepción cuando no existe, por lo que se comprueba con `hasattr`."""
    return hasattr(cita, "nota") and cita.nota is not None


def _cerrar_renglones(request, cita):
    """Cierra los renglones del plan que esta cita atendió y avanza el plan.

    Al atenderse la cita, el renglón presupuestado queda ejecutado: el avance
    del plan no depende de que alguien lo marque a mano.
    """
    renglones = list(
        cita.renglones_plan.filter(estado=True)
        .exclude(estado_detalle__in=("COMPLETADO", "ANULADO"))
        .select_related("plan")
    )
    for renglon in renglones:
        renglon.estado_detalle = "COMPLETADO"
        renglon.save(update_fields=["estado_detalle"])
    for plan in {r.plan for r in renglones}:
        estado = plan.actualizar_avance()
        messages.info(
            request,
            f"Plan {plan.codigo}: {plan.avance}% ejecutado "
            f"({plan.get_estado_plan_display().lower()}).",
        )
        if estado == "FINALIZADO" and plan.saldo > 0:
            messages.warning(
                request,
                f"El plan {plan.codigo} quedó finalizado con "
                f"un saldo de Q{plan.saldo:.2f} por cobrar.",
            )


@login_required
@escritura_requerida("agenda")
def registrar_tiempos(request, pk):
    """Registro de los tiempos reales de atención al cerrar la cita."""
    cita = get_object_or_404(Cita, pk=pk, estado=True)
    if request.method == "POST":
        form = RegistrarTiemposForm(request.POST, instance=cita)
        if form.is_valid():
            HistorialCita.objects.create(
                cita_ref=cita.pk,
                paciente=str(cita.paciente),
                odontologo=str(cita.odontologo),
                fecha_cita=cita.fecha,
                estado_cita_anterior=cita.estado_cita,
                accion="ATENCION",
                realizado_por=request.user.username,
            )
            cita = form.save()
            registrar_dato_entrenamiento(cita)
            messages.success(
                request,
                f"Atención registrada: {cita.duracion_real_min} minutos reales "
                f"frente a {cita.duracion_asignada_min} asignados. "
                f"El dato se incorporó al entrenamiento del modelo.",
            )
            _cerrar_renglones(request, cita)
            # El expediente del paciente queda incompleto sin la nota de la
            # visita, así que se ofrece escribirla en el momento a quien tiene
            # competencia para hacerlo.
            if request.user.puede_escribir("clinico") and not _tiene_nota(cita):
                return redirect(
                    f'{reverse("clinico:nota_nueva", args=[cita.paciente_id])}'
                    f"?cita={cita.pk}"
                )
            return redirect("agenda:lista")
    else:
        form = RegistrarTiemposForm(instance=cita)
    return render(request, "agenda/tiempos.html", {"form": form, "cita": cita})


@login_required
@modulo_requerido("agenda")
def ausencias(request, odontologo_id):
    """Ausencias puntuales de un odontólogo: excepciones a su patrón semanal.

    Lo puede administrar quien tenga escritura en la agenda y, además, el
    propio odontólogo sobre su ficha: su rol es de consulta para la agenda de
    la clínica, pero sus ausencias son información suya.
    """
    odontologo = get_object_or_404(Odontologo, pk=odontologo_id)
    if not puede_gestionar_odontologo(request.user, odontologo):
        raise PermissionDenied("Solo puede registrar sus propias ausencias.")

    if request.method == "POST":
        form = AusenciaForm(request.POST, odontologo=odontologo)
        if form.is_valid():
            ausencia = form.save(commit=False)
            ausencia.registrada_por = request.user.username
            ausencia.save()
            afectadas = (
                Cita.objects.filter(
                    odontologo=odontologo, fecha=ausencia.fecha, estado=True
                )
                .exclude(estado_cita="CANCELADA")
                .filter(
                    hora_inicio_programada__lt=ausencia.hora_fin,
                    hora_fin_programada__gt=ausencia.hora_inicio,
                )
                .count()
            )
            messages.success(
                request,
                f"Ausencia registrada para el "
                f'{ausencia.fecha.strftime("%d/%m/%Y")}.',
            )
            if afectadas:
                messages.warning(
                    request,
                    f'Atención: {afectadas} cita{"s" if afectadas != 1 else ""} ya '
                    f'programada{"s" if afectadas != 1 else ""} cae'
                    f'{"n" if afectadas != 1 else ""} dentro de esa ausencia. '
                    f"La ausencia no las cancela: debe reprogramarlas.",
                )
            return redirect("agenda:ausencias", odontologo_id=odontologo.pk)
    else:
        form = AusenciaForm(odontologo=odontologo)

    hoy = timezone.localdate()
    registradas = AusenciaOdontologo.objects.filter(
        odontologo=odontologo, estado=True
    ).order_by("-fecha")
    return render(
        request,
        "agenda/ausencias.html",
        {
            "odontologo": odontologo,
            "form": form,
            "proximas": [a for a in registradas if a.fecha >= hoy],
            "pasadas": [a for a in registradas if a.fecha < hoy][:10],
        },
    )


@login_required
@modulo_requerido("agenda")
def quitar_ausencia(request, pk):
    """Retira una ausencia mediante borrado lógico."""
    ausencia = get_object_or_404(AusenciaOdontologo, pk=pk)
    if not puede_gestionar_odontologo(request.user, ausencia.odontologo):
        raise PermissionDenied("Solo puede retirar sus propias ausencias.")
    if request.method == "POST":
        ausencia.estado = False
        ausencia.save(update_fields=["estado"])
        messages.success(
            request, f"Ausencia del " f'{ausencia.fecha.strftime("%d/%m/%Y")} retirada.'
        )
    return redirect("agenda:ausencias", odontologo_id=ausencia.odontologo_id)

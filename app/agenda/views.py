"""Módulo Principal y módulo de Agenda y Citas.

La vista `principal` es la pantalla de inicio del sistema: presenta los
indicadores operativos del día y el calendario semanal de la clínica.
"""
from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Odontologo
from inteligencia.servicio import (estimar_duracion, registrar_dato_entrenamiento,
                                   registrar_prediccion)
from pacientes.models import Paciente
from usuarios.decorators import escritura_requerida, modulo_requerido

from .forms import CitaForm, HorarioForm, RegistrarTiemposForm, hay_traslape
from .models import Cita, HistorialCita, HorarioDisponibilidad

DIAS = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
NOMBRES_DIA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado',
               'Domingo']
HORA_APERTURA = 7
HORA_CIERRE = 19

CLASES_ESTADO = {
    'PROGRAMADA': 'cita-prog',
    'ATENDIDA': 'cita-aten',
    'CANCELADA': 'cita-canc',
    'REPROGRAMADA': 'cita-reprog',
}


# ══════════════════════════════ utilidades ══════════════════════════════
def _lunes_de(fecha):
    return fecha - timedelta(days=fecha.weekday())


def _semana_solicitada(request):
    """Lee la semana del parámetro ?semana=AAAA-MM-DD; por omisión, la actual."""
    texto = request.GET.get('semana')
    if texto:
        try:
            return _lunes_de(datetime.strptime(texto, '%Y-%m-%d').date())
        except ValueError:
            pass
    return _lunes_de(timezone.localdate())


def _fecha_solicitada(request, parametro='fecha'):
    """Lee una fecha de la consulta; por omisión, la de hoy."""
    texto = request.GET.get(parametro)
    if texto:
        try:
            return datetime.strptime(texto, '%Y-%m-%d').date()
        except ValueError:
            pass
    return timezone.localdate()


def _minutos_disponibles(odontologos, dias):
    """Minutos de atención declarados por los odontólogos en los días indicados.

    `dias` es la lista de fechas que abarca la vista, de modo que el
    denominador de la utilización corresponda al período mostrado y no a una
    semana fija.
    """
    codigos = [DIAS[d.weekday()] for d in dias]
    total = 0
    franjas = HorarioDisponibilidad.objects.filter(estado=True,
                                                   odontologo__in=odontologos)
    for f in franjas:
        repeticiones = codigos.count(f.dia_semana)
        if repeticiones:
            inicio = datetime.combine(date.today(), f.hora_inicio)
            fin = datetime.combine(date.today(), f.hora_fin)
            total += repeticiones * max(0, int((fin - inicio).total_seconds() // 60))
    return total


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

    franjas_por_dia = {}
    for f in HorarioDisponibilidad.objects.filter(odontologo=odontologo, estado=True):
        franjas_por_dia.setdefault(f.dia_semana, []).append(f)

    ocupadas = {}
    for c in (Cita.objects
              .filter(odontologo=odontologo, fecha__in=fechas, estado=True)
              .exclude(estado_cita='CANCELADA')):
        ocupadas.setdefault(c.fecha, []).append((c.hora_inicio_programada,
                                                 c.hora_fin_programada))

    sugeridos = {}
    for indice, fecha in enumerate(fechas):
        for franja in franjas_por_dia.get(DIAS[fecha.weekday()], []):
            candidato = datetime.combine(fecha, franja.hora_inicio)
            limite = datetime.combine(fecha, franja.hora_fin)
            while candidato + timedelta(minutes=duracion) <= limite:
                inicio_h = candidato.time()
                fin_h = (candidato + timedelta(minutes=duracion)).time()
                ya_paso = fecha < hoy or (fecha == hoy and inicio_h < ahora)
                choca = any(hay_traslape(inicio_h, fin_h, oi, of)
                            for oi, of in ocupadas.get(fecha, []))
                clave = (indice, inicio_h.hour)
                if not ya_paso and not choca and clave not in sugeridos:
                    sugeridos[clave] = inicio_h.strftime('%H:%M')
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
            celdas.append({
                'indice': d,
                'citas': rejilla.get(hora, {}).get(d, []),
                'fecha': fecha.isoformat(),
                'hora': f'{hora:02d}:00',
                'sugerida': (sugeridos or {}).get((d, hora)),
            })
        filas.append({'hora': f'{hora:02d}:00', 'celdas': celdas})
    return filas


# ══════════════════════════ MÓDULO PRINCIPAL ══════════════════════════
@login_required
@modulo_requerido('agenda')
def principal(request):
    """Pantalla de inicio: indicadores y calendario, por semana o por día."""
    hoy = timezone.localdate()
    vista = 'dia' if request.GET.get('vista') == 'dia' else 'semana'

    if vista == 'dia':
        inicio = _fecha_solicitada(request)
        dias_visibles = 1
        anterior = inicio - timedelta(days=1)
        siguiente = inicio + timedelta(days=1)
        es_periodo_actual = inicio == hoy
    else:
        inicio = _lunes_de(_fecha_solicitada(request, 'semana'))
        dias_visibles = 6
        anterior = inicio - timedelta(days=7)
        siguiente = inicio + timedelta(days=7)
        es_periodo_actual = inicio == _lunes_de(hoy)
    fin = inicio + timedelta(days=dias_visibles - 1)
    fechas = [inicio + timedelta(days=i) for i in range(dias_visibles)]

    odontologos = Odontologo.objects.filter(estado=True)
    filtro_odontologo = request.GET.get('odontologo', '')

    citas = (Cita.objects
             .filter(fecha__range=(inicio, fin), estado=True)
             .select_related('paciente', 'odontologo', 'procedimiento')
             .order_by('fecha', 'hora_inicio_programada'))
    if filtro_odontologo.isdigit():
        citas = citas.filter(odontologo_id=int(filtro_odontologo))
        odontologos_kpi = odontologos.filter(id=int(filtro_odontologo))
    else:
        odontologos_kpi = odontologos

    for cita in citas:
        cita.clase_css = CLASES_ESTADO.get(cita.estado_cita, 'cita-prog')

    # --- recomendación de bloques: dónde cabe el procedimiento elegido ---
    from catalogo.models import Procedimiento
    procedimientos = Procedimiento.objects.filter(estado=True)
    id_proc = request.GET.get('procedimiento', '')
    piezas = request.GET.get('piezas', '1')
    piezas = int(piezas) if piezas.isdigit() and int(piezas) > 0 else 1
    estimacion = None
    sugeridos = {}
    odontologo_sug = (odontologos.filter(id=int(filtro_odontologo)).first()
                      if filtro_odontologo.isdigit() else None)
    procedimiento_sug = (procedimientos.filter(pk=int(id_proc)).first()
                         if id_proc.isdigit() else None)
    if procedimiento_sug and odontologo_sug:
        estimacion = estimar_duracion(procedimiento_sug, odontologo_sug,
                                      inicio, time(9, 0), piezas)
        sugeridos = _huecos_sugeridos(odontologo_sug, fechas,
                                      estimacion.duracion_min, hoy,
                                      timezone.localtime().time())

    # --- indicadores ---
    citas_hoy = sum(1 for c in citas if c.fecha == hoy and c.estado_cita != 'CANCELADA')
    minutos_ocupados = (citas.exclude(estado_cita='CANCELADA')
                        .aggregate(total=Sum('duracion_asignada_min'))['total'] or 0)
    minutos_disponibles = _minutos_disponibles(odontologos_kpi, fechas)
    utilizacion = round(minutos_ocupados / minutos_disponibles * 100) if minutos_disponibles else 0

    desviacion = (Cita.objects
                  .filter(estado_cita='ATENDIDA', duracion_real_min__isnull=False, estado=True)
                  .aggregate(promedio_real=Avg('duracion_real_min'),
                             promedio_asignado=Avg('duracion_asignada_min'),
                             total=Count('id')))
    if desviacion['total']:
        error_medio = round(abs((desviacion['promedio_real'] or 0) -
                                (desviacion['promedio_asignado'] or 0)), 1)
    else:
        error_medio = None

    contexto = {
        'vista': vista,
        'inicio': inicio,
        'fin': fin,
        'parametro_periodo': 'fecha' if vista == 'dia' else 'semana',
        'periodo_anterior': anterior.isoformat(),
        'periodo_siguiente': siguiente.isoformat(),
        'periodo_hoy': (hoy if vista == 'dia' else _lunes_de(hoy)).isoformat(),
        'es_periodo_actual': es_periodo_actual,
        'dias': [{'nombre': NOMBRES_DIA[f.weekday()], 'fecha': f, 'es_hoy': f == hoy}
                 for f in fechas],
        'filas': _rejilla(citas, inicio, dias_visibles, sugeridos),
        'procedimientos': procedimientos,
        'procedimiento_sug': id_proc,
        'piezas': piezas,
        'estimacion': estimacion,
        'odontologo_sug': odontologo_sug,
        'total_sugeridos': len(sugeridos),
        'odontologos': odontologos,
        'filtro_odontologo': filtro_odontologo,
        'kpi_citas_hoy': citas_hoy,
        'kpi_utilizacion': utilizacion,
        'kpi_pacientes': Paciente.objects.filter(estado=True).count(),
        'kpi_error_medio': error_medio,
        'kpi_citas_periodo': citas.exclude(estado_cita='CANCELADA').count(),
    }
    return render(request, 'agenda/principal.html', contexto)


# ══════════════════════════ AGENDA Y CITAS ══════════════════════════
@login_required
@modulo_requerido('agenda')
def lista(request):
    """Consulta de citas por rango de fechas, odontólogo y estado."""
    hoy = timezone.localdate()
    desde = request.GET.get('desde') or _lunes_de(hoy).isoformat()
    hasta = request.GET.get('hasta') or (_lunes_de(hoy) + timedelta(days=6)).isoformat()
    odontologo = request.GET.get('odontologo', '')
    estado_cita = request.GET.get('estado_cita', '')

    citas = (Cita.objects.filter(estado=True)
             .select_related('paciente', 'odontologo', 'procedimiento')
             .order_by('-fecha', 'hora_inicio_programada'))
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

    return render(request, 'agenda/lista.html', {
        'citas': citas[:200],
        'desde': desde, 'hasta': hasta,
        'odontologo': odontologo, 'estado_cita': estado_cita,
        'odontologos': Odontologo.objects.filter(estado=True),
        'estados': Cita.ESTADOS,
    })


@login_required
@modulo_requerido('agenda')
def detalle(request, pk):
    """Ficha de una cita, con las acciones disponibles según su estado.

    Es el destino al pulsar una cita en el calendario: reúne en un solo lugar
    la reprogramación, el registro de la atención y la cancelación, que antes
    estaban repartidas entre el listado y la propia rejilla.
    """
    cita = get_object_or_404(
        Cita.objects.select_related('paciente', 'odontologo', 'procedimiento'), pk=pk)

    prediccion = cita.predicciones.select_related('modelo').order_by('-fecha').first()
    abierta = cita.estado_cita in ('PROGRAMADA', 'REPROGRAMADA')
    desvio = None
    if cita.duracion_real_min:
        desvio = cita.duracion_real_min - cita.duracion_asignada_min

    return render(request, 'agenda/detalle.html', {
        'cita': cita,
        'prediccion': prediccion,
        'abierta': abierta,
        'desvio': desvio,
        'volver': request.GET.get('volver') or reverse('agenda:principal'),
    })


def _estimacion_para(form):
    """Calcula la estimación de duración con los datos que ya tiene el formulario."""
    datos = form.data if form.is_bound else {}
    try:
        from catalogo.models import Odontologo as Odo, Procedimiento as Proc
        id_proc = (datos.get('procedimiento') or '').strip()
        id_odo = (datos.get('odontologo') or '').strip()
        if not (id_proc.isdigit() and id_odo.isdigit()):
            return None
        procedimiento = Proc.objects.filter(pk=int(id_proc)).first()
        odontologo = Odo.objects.filter(pk=int(id_odo)).first()
        if not (procedimiento and odontologo):
            return None
        fecha = datetime.strptime(datos.get('fecha'), '%Y-%m-%d').date()
        hora = datetime.strptime(datos.get('hora_inicio_programada'), '%H:%M').time()
        piezas = int(datos.get('num_piezas') or 1)
    except (ValueError, TypeError):
        return None
    return estimar_duracion(procedimiento, odontologo, fecha, hora, piezas)


@login_required
@modulo_requerido('agenda')
def estimar(request):
    """Devuelve la estimación de duración en formato JSON.

    La consulta el formulario de cita cada vez que cambian el procedimiento, el
    odontólogo, la fecha, la hora o el número de piezas, de modo que el usuario
    vea la recomendación antes de decidir la duración.
    """
    from django.http import JsonResponse
    from catalogo.models import Odontologo as Odo, Procedimiento as Proc

    id_proc = (request.GET.get('procedimiento') or '').strip()
    id_odo = (request.GET.get('odontologo') or '').strip()
    if not (id_proc.isdigit() and id_odo.isdigit()):
        return JsonResponse({'disponible': False})

    procedimiento = Proc.objects.filter(pk=int(id_proc), estado=True).first()
    odontologo = Odo.objects.filter(pk=int(id_odo), estado=True).first()
    if not (procedimiento and odontologo):
        return JsonResponse({'disponible': False})

    try:
        fecha = datetime.strptime(request.GET.get('fecha'), '%Y-%m-%d').date()
        hora = datetime.strptime(request.GET.get('hora'), '%H:%M').time()
    except (ValueError, TypeError):
        fecha, hora = timezone.localdate(), time(9, 0)

    piezas = int(request.GET.get('piezas') or 1)
    est = estimar_duracion(procedimiento, odontologo, fecha, hora, piezas)
    return JsonResponse({
        'disponible': True,
        'duracion': est.duracion_min,
        'bloque_min': est.bloque_min,
        'bloque_max': est.bloque_max,
        'origen': est.origen,
        'etiqueta_origen': est.etiqueta_origen,
        'detalle': est.detalle,
    })


@login_required
@escritura_requerida('agenda')
def crear(request):
    estimacion = None
    if request.method == 'POST':
        form = CitaForm(request.POST)
        estimacion = _estimacion_para(form)
        if form.is_valid():
            cita = form.save()
            if estimacion:
                registrar_prediccion(cita, estimacion)
            HistorialCita.objects.create(
                cita_ref=cita.pk, paciente=str(cita.paciente),
                odontologo=str(cita.odontologo), fecha_cita=cita.fecha,
                estado_cita_anterior='', accion='CREACION',
                realizado_por=request.user.username)
            messages.success(request, f'Cita programada para {cita.paciente} '
                                      f'el {cita.fecha.strftime("%d/%m/%Y")} '
                                      f'a las {cita.hora_inicio_programada.strftime("%H:%M")}.')
            return redirect('agenda:principal')
    else:
        inicial = {}
        if request.GET.get('fecha'):
            inicial['fecha'] = request.GET['fecha']
        if request.GET.get('hora'):
            inicial['hora_inicio_programada'] = request.GET['hora']
        # Al programar desde una casilla del calendario, el odontólogo del
        # filtro activo viene preseleccionado.
        if request.GET.get('odontologo', '').isdigit():
            inicial['odontologo'] = int(request.GET['odontologo'])
        if request.GET.get('procedimiento', '').isdigit():
            inicial['procedimiento'] = int(request.GET['procedimiento'])
        form = CitaForm(initial=inicial)

    return render(request, 'agenda/form.html', {
        'form': form, 'titulo': 'Programar nueva cita',
        'estimacion': estimacion, 'es_nueva': True,
    })


@login_required
@escritura_requerida('agenda')
def editar(request, pk):
    """Reprogramación de una cita existente."""
    cita = get_object_or_404(Cita, pk=pk, estado=True)
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        estimacion = _estimacion_para(form)
        if form.is_valid():
            HistorialCita.objects.create(
                cita_ref=cita.pk, paciente=str(cita.paciente),
                odontologo=str(cita.odontologo), fecha_cita=cita.fecha,
                estado_cita_anterior=cita.estado_cita, accion='REPROGRAMACION',
                realizado_por=request.user.username)
            cita = form.save()
            if cita.estado_cita == 'PROGRAMADA':
                cita.estado_cita = 'REPROGRAMADA'
                cita.save(update_fields=['estado_cita'])
            messages.success(request, 'La cita fue reprogramada correctamente.')
            return redirect('agenda:principal')
    else:
        form = CitaForm(instance=cita)
        estimacion = estimar_duracion(cita.procedimiento, cita.odontologo,
                                      cita.fecha, cita.hora_inicio_programada)

    return render(request, 'agenda/form.html', {
        'form': form, 'titulo': f'Reprogramar cita de {cita.paciente}',
        'estimacion': estimacion, 'cita': cita, 'es_nueva': False,
    })


@login_required
@escritura_requerida('agenda')
def cancelar(request, pk):
    """Cancelación de una cita: cambia su estado y conserva el registro."""
    cita = get_object_or_404(Cita, pk=pk, estado=True)
    if request.method == 'POST':
        HistorialCita.objects.create(
            cita_ref=cita.pk, paciente=str(cita.paciente),
            odontologo=str(cita.odontologo), fecha_cita=cita.fecha,
            estado_cita_anterior=cita.estado_cita, accion='CANCELACION',
            realizado_por=request.user.username)
        motivo = request.POST.get('motivo', '').strip()
        cita.estado_cita = 'CANCELADA'
        if motivo:
            cita.observaciones = (cita.observaciones + f'\nCancelación: {motivo}').strip()
        cita.save(update_fields=['estado_cita', 'observaciones'])
        messages.success(request, f'La cita de {cita.paciente} fue cancelada.')
    return redirect(request.POST.get('siguiente') or 'agenda:principal')


@login_required
@escritura_requerida('agenda')
def horarios(request, odontologo_id):
    """Configuración de las franjas de atención de un odontólogo.

    Sin franjas registradas el sistema rechaza todas sus citas, por lo que esta
    pantalla es el paso obligatorio tras dar de alta a un profesional.
    """
    odontologo = get_object_or_404(Odontologo, pk=odontologo_id)

    if request.method == 'POST':
        form = HorarioForm(request.POST, odontologo=odontologo)
        if form.is_valid():
            creadas = form.guardar()
            if creadas:
                messages.success(
                    request,
                    f'{len(creadas)} franja{"s" if len(creadas) != 1 else ""} '
                    f'de atención registrada{"s" if len(creadas) != 1 else ""} '
                    f'para {odontologo}.')
            else:
                messages.info(request, 'Esa franja ya estaba registrada.')
            return redirect('agenda:horarios', odontologo_id=odontologo.pk)
    else:
        form = HorarioForm(odontologo=odontologo)

    # Franjas agrupadas por día, para presentarlas como una semana
    franjas = (HorarioDisponibilidad.objects
               .filter(odontologo=odontologo, estado=True)
               .order_by('hora_inicio'))
    etiquetas = dict(HorarioDisponibilidad.DIAS)
    semana = []
    for codigo in DIAS[:6]:
        del_dia = [f for f in franjas if f.dia_semana == codigo]
        minutos = sum(
            (datetime.combine(date.today(), f.hora_fin) -
             datetime.combine(date.today(), f.hora_inicio)).seconds // 60
            for f in del_dia)
        semana.append({'codigo': codigo, 'nombre': etiquetas.get(codigo, codigo),
                       'franjas': del_dia, 'horas': round(minutos / 60, 1)})

    return render(request, 'agenda/horarios.html', {
        'odontologo': odontologo,
        'semana': semana,
        'form': form,
        'total_franjas': franjas.count(),
        'horas_semana': round(sum(d['horas'] for d in semana), 1),
    })


@login_required
@escritura_requerida('agenda')
def quitar_horario(request, pk):
    """Retira una franja de disponibilidad mediante borrado lógico.

    Si la franja tiene citas futuras dentro de ella, se informa al usuario:
    las citas ya programadas se conservan, pero no podrán reprogramarse en ese
    rango mientras la franja siga retirada.
    """
    franja = get_object_or_404(HorarioDisponibilidad, pk=pk)
    odontologo_id = franja.odontologo.pk

    if request.method == 'POST':
        indice_dia = DIAS.index(franja.dia_semana) if franja.dia_semana in DIAS else None
        afectadas = 0
        if indice_dia is not None:
            afectadas = Cita.objects.filter(
                odontologo=franja.odontologo,
                fecha__gte=timezone.localdate(),
                hora_inicio_programada__gte=franja.hora_inicio,
                hora_fin_programada__lte=franja.hora_fin,
                estado=True,
            ).exclude(estado_cita='CANCELADA').count()

        franja.estado = False
        franja.save(update_fields=['estado'])

        if afectadas:
            messages.warning(
                request,
                f'Franja retirada. Atención: hay {afectadas} cita'
                f'{"s" if afectadas != 1 else ""} futura'
                f'{"s" if afectadas != 1 else ""} dentro de ese horario; '
                f'se conservan, pero no podrán reprogramarse en ese rango.')
        else:
            messages.success(request, 'Franja de atención retirada.')

    return redirect('agenda:horarios', odontologo_id=odontologo_id)


@login_required
@escritura_requerida('agenda')
def registrar_tiempos(request, pk):
    """Registro de los tiempos reales de atención al cerrar la cita."""
    cita = get_object_or_404(Cita, pk=pk, estado=True)
    if request.method == 'POST':
        form = RegistrarTiemposForm(request.POST, instance=cita)
        if form.is_valid():
            HistorialCita.objects.create(
                cita_ref=cita.pk, paciente=str(cita.paciente),
                odontologo=str(cita.odontologo), fecha_cita=cita.fecha,
                estado_cita_anterior=cita.estado_cita, accion='ATENCION',
                realizado_por=request.user.username)
            cita = form.save()
            registrar_dato_entrenamiento(cita)
            messages.success(
                request,
                f'Atención registrada: {cita.duracion_real_min} minutos reales '
                f'frente a {cita.duracion_asignada_min} asignados. '
                f'El dato se incorporó al entrenamiento del modelo.')
            return redirect('agenda:lista')
    else:
        form = RegistrarTiemposForm(instance=cita)
    return render(request, 'agenda/tiempos.html', {'form': form, 'cita': cita})

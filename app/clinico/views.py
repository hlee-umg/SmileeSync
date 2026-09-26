"""Módulo de Expediente Clínico y cobros.

Se apoya en dos permisos distintos, porque son dos competencias distintas:

    `clinico`  — el expediente. Lo consulta quien atiende o agenda; lo escribe
                 quien tiene competencia profesional (véase
                 `Rol.escritura_clinica`), no quien tiene más privilegios
                 administrativos.
    `finanzas` — los cobros. Los registra la recepción, que es quien cobra, y
                 no el odontólogo.
"""
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from pacientes.models import Paciente
from usuarios.decorators import escritura_requerida, modulo_requerido

from .forms import (DetallePlanForm, HallazgoForm, NotaClinicaForm, PagoForm,
                   PlanTratamientoForm)
from .models import (DetallePlan, Hallazgo, HistorialPlan, NotaClinica, Pago,
                     PlanTratamiento, odontograma_vigente)
from .piezas import filas_arcada, nombre as nombre_pieza


def _exigir_escritura_clinica(request):
    """Comprueba la escritura del expediente sin depender de la plantilla."""
    if not request.user.puede_escribir('clinico'):
        raise PermissionDenied(
            'El expediente clínico solo lo registra el personal odontológico.')


def _resumen_odontograma(paciente):
    """Cifras del odontograma que encabezan el expediente."""
    vigente = odontograma_vigente(paciente)
    hallazgos = [h for caras in vigente.values() for h in caras.values()]
    return {
        'piezas_registradas': len(vigente),
        'patologicos': sum(1 for h in hallazgos if h.es_patologico),
        'tratadas': sum(1 for h in hallazgos if h.tipo in Hallazgo.TRATADOS),
        'ausentes': sum(1 for h in hallazgos if h.tipo == 'AUSENTE'),
    }


# ════════════════════════════ EXPEDIENTES ════════════════════════════
@login_required
@modulo_requerido('clinico')
def lista(request):
    """Pacientes con su actividad clínica, para entrar al expediente."""
    q = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.filter(estado=True)
    if q:
        pacientes = pacientes.filter(
            Q(codigo__icontains=q) | Q(nombres__icontains=q) |
            Q(apellidos__icontains=q) | Q(telefono__icontains=q))
    pacientes = (pacientes
                 .annotate(num_notas=Count('notas', filter=Q(notas__estado=True),
                                           distinct=True),
                           num_planes=Count('planes', filter=Q(planes__estado=True),
                                            distinct=True),
                           num_hallazgos=Count('hallazgos',
                                               filter=Q(hallazgos__estado=True),
                                               distinct=True))
                 .order_by('apellidos', 'nombres'))

    return render(request, 'clinico/lista.html', {
        'pacientes': pacientes[:200],
        'q': q,
        'con_expediente': sum(1 for p in pacientes if p.num_notas or p.num_hallazgos),
    })


@login_required
@modulo_requerido('clinico')
def expediente(request, paciente_id):
    """Vista única del expediente: odontograma, evolución, planes y saldo."""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    planes = (PlanTratamiento.objects
              .filter(paciente=paciente, estado=True)
              .select_related('odontologo')
              .prefetch_related('detalles', 'pagos'))
    notas = (NotaClinica.objects
             .filter(paciente=paciente, estado=True)
             .select_related('odontologo', 'cita')[:15])

    saldo = sum((p.saldo for p in planes if p.estado_plan in PlanTratamiento.ABIERTOS),
                Decimal('0.00'))

    return render(request, 'clinico/expediente.html', {
        'paciente': paciente,
        'seccion': 'resumen',
        'resumen': _resumen_odontograma(paciente),
        'planes': planes,
        'notas': notas,
        'total_notas': NotaClinica.objects.filter(paciente=paciente, estado=True).count(),
        'saldo': saldo,
        'antecedentes': paciente.antecedentes.filter(estado=True),
        'citas': (paciente.citas.filter(estado=True)
                  .select_related('procedimiento', 'odontologo')
                  .order_by('-fecha')[:8]),
    })


# ════════════════════════════ ODONTOGRAMA ════════════════════════════
@login_required
@modulo_requerido('clinico')
def odontograma(request, paciente_id):
    """Odontograma del paciente: estado vigente de cada pieza y su historial.

    La arcada se dibuja completa (32 piezas permanentes) y cada pieza muestra el
    hallazgo vigente. Registrar un hallazgo no modifica el anterior: se agrega
    uno nuevo, de modo que el expediente conserve la evolución de la pieza.
    """
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    seleccionada = request.GET.get('pieza', '')

    if request.method == 'POST':
        _exigir_escritura_clinica(request)
        form = HallazgoForm(request.POST)
        if form.is_valid():
            hallazgo = form.save(commit=False)
            hallazgo.paciente = paciente
            hallazgo.registrado_por = request.user.username
            hallazgo.save()
            messages.success(
                request,
                f'Hallazgo registrado en la pieza {hallazgo.pieza} '
                f'({hallazgo.get_tipo_display().lower()}).')
            return redirect(f'{reverse("clinico:odontograma", args=[paciente.pk])}'
                            f'?pieza={hallazgo.pieza}')
    else:
        inicial = {}
        if seleccionada.isdigit():
            inicial['pieza'] = int(seleccionada)
        form = HallazgoForm(initial=inicial)

    vigente = odontograma_vigente(paciente)
    cuadrantes = []
    for fila in filas_arcada():
        piezas = []
        for numero in fila['piezas']:
            caras = vigente.get(numero, {})
            # El hallazgo que define el color de la pieza: el de toda la pieza
            # si existe, y si no el más grave de sus caras.
            principal = caras.get('TODA')
            if principal is None and caras:
                principal = next((h for h in caras.values() if h.es_patologico),
                                 next(iter(caras.values())))
            piezas.append({
                'numero': numero,
                'nombre': nombre_pieza(numero),
                'hallazgo': principal,
                'caras': len(caras),
                'clase': principal.clase_css if principal else '',
                'es_seleccionada': str(numero) == seleccionada,
            })
        cuadrantes.append({'nombre': fila['nombre'], 'piezas': piezas})

    detalle_pieza = None
    if seleccionada.isdigit():
        detalle_pieza = {
            'numero': int(seleccionada),
            'nombre': nombre_pieza(int(seleccionada)),
            'caras': vigente.get(int(seleccionada), {}),
            'historial': (Hallazgo.objects
                          .filter(paciente=paciente, pieza=int(seleccionada),
                                  estado=True)
                          .order_by('-fecha', '-creado')),
        }

    return render(request, 'clinico/odontograma.html', {
        'paciente': paciente,
        'seccion': 'odontograma',
        'cuadrantes': cuadrantes,
        'form': form,
        'pieza': detalle_pieza,
        'resumen': _resumen_odontograma(paciente),
    })


@login_required
@modulo_requerido('clinico')
def quitar_hallazgo(request, pk):
    """Retira un hallazgo mal registrado mediante borrado lógico.

    Al retirarlo, el hallazgo vigente de esa pieza vuelve a ser el anterior, que
    sigue en la tabla: por eso el registro no se elimina.
    """
    hallazgo = get_object_or_404(Hallazgo, pk=pk)
    _exigir_escritura_clinica(request)
    paciente_pk, pieza = hallazgo.paciente_id, hallazgo.pieza
    if request.method == 'POST':
        hallazgo.estado = False
        hallazgo.save(update_fields=['estado'])
        messages.success(request, f'Hallazgo retirado de la pieza {pieza}.')
    return redirect(f'{reverse("clinico:odontograma", args=[paciente_pk])}?pieza={pieza}')


# ═══════════════════════════ NOTAS CLÍNICAS ═══════════════════════════
@login_required
@modulo_requerido('clinico')
def notas(request, paciente_id):
    """Evolución completa del paciente, visita por visita."""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    registradas = (NotaClinica.objects
                   .filter(paciente=paciente, estado=True)
                   .select_related('odontologo', 'cita', 'cita__procedimiento')
                   .prefetch_related('hallazgos'))
    return render(request, 'clinico/notas.html', {
        'paciente': paciente,
        'seccion': 'notas',
        'notas': registradas,
        'con_complicacion': registradas.filter(complicacion=True).count(),
    })


@login_required
@modulo_requerido('clinico')
def nota_nueva(request, paciente_id):
    """Redacta la nota de una visita, opcionalmente ligada a una cita atendida.

    Cuando llega con ?cita=, los datos que la cita ya conoce —odontólogo, fecha
    y procedimiento— vienen precargados, de modo que el profesional solo escriba
    lo que únicamente él puede aportar.
    """
    from agenda.models import Cita

    paciente = get_object_or_404(Paciente, pk=paciente_id)
    _exigir_escritura_clinica(request)

    id_cita = request.GET.get('cita', '')
    cita = None
    if id_cita.isdigit():
        cita = Cita.objects.filter(pk=int(id_cita), paciente=paciente,
                                   estado=True).first()
        if cita and hasattr(cita, 'nota') and cita.nota:
            messages.info(request, 'Esa cita ya tiene una nota clínica registrada.')
            return redirect('clinico:notas', paciente_id=paciente.pk)

    if request.method == 'POST':
        form = NotaClinicaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.paciente = paciente
            nota.registrado_por = request.user.username
            if cita:
                nota.cita = cita
            nota.save()
            messages.success(request, f'Nota clínica del '
                                      f'{nota.fecha.strftime("%d/%m/%Y")} registrada.')
            return redirect('clinico:notas', paciente_id=paciente.pk)
    else:
        inicial = {}
        if cita:
            inicial = {
                'odontologo': cita.odontologo_id,
                'fecha': cita.fecha,
                'motivo': cita.procedimiento.nombre,
                'procedimiento_realizado': cita.procedimiento.nombre,
            }
        form = NotaClinicaForm(initial=inicial)

    return render(request, 'clinico/nota_form.html', {
        'paciente': paciente,
        'seccion': 'notas',
        'form': form,
        'cita': cita,
    })


# ═════════════════════════ PLANES DE TRATAMIENTO ═════════════════════════
@login_required
@modulo_requerido('clinico')
def planes(request):
    """Listado general de planes, con su avance y su saldo."""
    estado_plan = request.GET.get('estado_plan', '')
    q = request.GET.get('q', '').strip()

    consulta = (PlanTratamiento.objects.filter(estado=True)
                .select_related('paciente', 'odontologo')
                .prefetch_related('detalles', 'pagos'))
    if estado_plan:
        consulta = consulta.filter(estado_plan=estado_plan)
    if q:
        consulta = consulta.filter(
            Q(codigo__icontains=q) | Q(paciente__nombres__icontains=q) |
            Q(paciente__apellidos__icontains=q))

    todos = list(consulta[:200])
    return render(request, 'clinico/planes.html', {
        'planes': todos,
        'estado_plan': estado_plan,
        'q': q,
        'estados': PlanTratamiento.ESTADOS,
        'minutos_comprometidos': sum(p.minutos_pendientes for p in todos
                                     if p.estado_plan in PlanTratamiento.ABIERTOS),
    })


@login_required
@modulo_requerido('clinico')
def plan_nuevo(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    _exigir_escritura_clinica(request)

    if request.method == 'POST':
        form = PlanTratamientoForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.paciente = paciente
            plan.creado_por = request.user.username
            plan.codigo = PlanTratamiento.siguiente_codigo()
            plan.save()
            HistorialPlan.registrar(plan, 'CREACION', request.user.username,
                                    estado_anterior='')
            messages.success(request, f'Plan {plan.codigo} creado. Agregue los '
                                      f'renglones del tratamiento.')
            return redirect('clinico:plan_detalle', pk=plan.pk)
    else:
        form = PlanTratamientoForm()

    return render(request, 'clinico/plan_form.html', {
        'paciente': paciente, 'seccion': 'planes', 'form': form,
        'titulo': f'Nuevo plan de tratamiento para {paciente.nombres}',
    })


@login_required
@modulo_requerido('clinico')
def plan_detalle(request, pk):
    """Detalle del plan: renglones, sesiones estimadas, presupuesto y abonos.

    Reúne en una pantalla las tres preguntas que el plan debe responder: qué se
    va a hacer, en cuántas sesiones cabe y cuánto se ha pagado.
    """
    plan = get_object_or_404(
        PlanTratamiento.objects.select_related('paciente', 'odontologo'), pk=pk)

    form_detalle = DetallePlanForm(plan=plan)
    form_pago = PagoForm(plan=plan)

    if request.method == 'POST':
        accion = request.POST.get('accion', 'renglon')
        if accion == 'pago':
            if not request.user.puede_escribir('finanzas'):
                raise PermissionDenied('No tiene permiso para registrar cobros.')
            form_pago = PagoForm(request.POST, plan=plan)
            if form_pago.is_valid():
                pago = form_pago.save(commit=False)
                pago.recibido_por = request.user.username
                pago.save()
                HistorialPlan.registrar(plan, 'PAGO', request.user.username,
                                        detalle=f'Abono de Q{pago.monto} '
                                                f'({pago.get_metodo_display()})')
                messages.success(request, f'Abono de Q{pago.monto} registrado. '
                                          f'Saldo: Q{plan.saldo:.2f}.')
                return redirect('clinico:plan_detalle', pk=plan.pk)
        else:
            _exigir_escritura_clinica(request)
            if plan.estado_plan in ('FINALIZADO', 'RECHAZADO'):
                messages.error(request, 'Un plan cerrado no admite renglones nuevos.')
                return redirect('clinico:plan_detalle', pk=plan.pk)
            form_detalle = DetallePlanForm(request.POST, plan=plan)
            if form_detalle.is_valid():
                detalle = form_detalle.save()
                HistorialPlan.registrar(
                    plan, 'ACTUALIZACION', request.user.username,
                    detalle=f'Renglón agregado: {detalle}')
                messages.success(
                    request,
                    f'Renglón agregado. El modelo estima '
                    f'{detalle.duracion_estimada_min} minutos '
                    f'({detalle.etiqueta_origen.lower()}).')
                return redirect('clinico:plan_detalle', pk=plan.pk)

    return render(request, 'clinico/plan_detalle.html', {
        'plan': plan,
        'paciente': plan.paciente,
        'seccion': 'planes',
        'detalles': plan.detalles.filter(estado=True).select_related(
            'procedimiento', 'cita'),
        'sesiones': plan.sesiones_sugeridas(),
        'pagos': plan.pagos.filter(estado=True),
        'pagos_anulados': plan.pagos.filter(estado=False),
        'form_detalle': form_detalle,
        'form_pago': form_pago,
        # Tarifas del catálogo, para que la pantalla muestre el precio sugerido
        # al elegir el procedimiento en lugar de obligar a consultarlo aparte.
        'precios': {str(p.pk): str(p.precio)
                    for p in form_detalle.fields['procedimiento'].queryset},
        'historial': HistorialPlan.objects.filter(plan_ref=plan.pk)[:10],
    })


@login_required
@modulo_requerido('clinico')
def plan_quitar_detalle(request, pk):
    """Anula un renglón del plan sin borrarlo del presupuesto histórico."""
    detalle = get_object_or_404(DetallePlan, pk=pk)
    _exigir_escritura_clinica(request)
    plan = detalle.plan
    if request.method == 'POST':
        if detalle.estado_detalle == 'COMPLETADO':
            messages.error(request, 'Un renglón ya atendido no puede anularse.')
        else:
            detalle.estado_detalle = 'ANULADO'
            detalle.save(update_fields=['estado_detalle'])
            HistorialPlan.registrar(plan, 'ANULACION', request.user.username,
                                    detalle=f'Renglón anulado: {detalle}')
            messages.success(request, 'Renglón anulado del plan.')
    return redirect('clinico:plan_detalle', pk=plan.pk)


@login_required
@modulo_requerido('clinico')
def plan_estado(request, pk):
    """Aprobación, rechazo o cierre del plan.

    Un plan en borrador no reserva nada; al aprobarse pasa a ser un compromiso
    de tiempo de sillón, y por eso exige tener al menos un renglón.
    """
    plan = get_object_or_404(PlanTratamiento, pk=pk)
    _exigir_escritura_clinica(request)
    destino = request.POST.get('estado_plan', '')

    if request.method == 'POST' and destino in dict(PlanTratamiento.ESTADOS):
        if destino in PlanTratamiento.ABIERTOS and not plan.total_renglones:
            messages.error(request, 'Agregue al menos un renglón antes de aprobar '
                                    'el plan.')
            return redirect('clinico:plan_detalle', pk=plan.pk)

        anterior = plan.estado_plan
        plan.estado_plan = destino
        campos = ['estado_plan']
        if destino == 'APROBADO' and not plan.fecha_aprobacion:
            plan.fecha_aprobacion = timezone.localdate()
            campos.append('fecha_aprobacion')
        plan.save(update_fields=campos)

        accion = {'APROBADO': 'APROBACION', 'RECHAZADO': 'RECHAZO',
                  'FINALIZADO': 'FINALIZACION'}.get(destino, 'ACTUALIZACION')
        HistorialPlan.registrar(plan, accion, request.user.username,
                                detalle=f'{anterior} → {destino}',
                                estado_anterior=anterior)
        messages.success(request, f'El plan {plan.codigo} quedó como '
                                  f'«{plan.get_estado_plan_display()}».')
    return redirect('clinico:plan_detalle', pk=plan.pk)


@login_required
@escritura_requerida('agenda')
def agendar_renglon(request, pk):
    """Envía un renglón del plan al formulario de cita con sus datos precargados.

    Es el punto donde el plan deja de ser un documento: el procedimiento, el
    paciente, el odontólogo y la duración que el modelo estimó al presupuestar
    llegan ya puestos al formulario de la agenda.
    """
    detalle = get_object_or_404(
        DetallePlan.objects.select_related('plan', 'plan__paciente',
                                           'plan__odontologo', 'procedimiento'),
        pk=pk)
    plan = detalle.plan

    if detalle.estado_detalle == 'COMPLETADO':
        messages.info(request, 'Ese renglón ya fue atendido.')
        return redirect('clinico:plan_detalle', pk=plan.pk)
    if plan.estado_plan not in PlanTratamiento.ABIERTOS:
        messages.error(request, 'Solo se agendan renglones de un plan aprobado.')
        return redirect('clinico:plan_detalle', pk=plan.pk)

    parametros = {
        'paciente': plan.paciente_id,
        'odontologo': plan.odontologo_id,
        'procedimiento': detalle.procedimiento_id,
        'duracion': detalle.duracion_estimada_min,
        'piezas': detalle.num_piezas,
        'renglon': detalle.pk,
    }
    consulta = '&'.join(f'{k}={v}' for k, v in parametros.items())
    return redirect(f'{reverse("agenda:crear")}?{consulta}')


# ═══════════════════════════════ COBROS ═══════════════════════════════
@login_required
@modulo_requerido('finanzas')
def cobros(request):
    """Estado de cuenta de los planes vigentes: qué queda por cobrar.

    Es la pantalla de la recepción: parte del plan aprobado, resta los abonos
    vigentes y ordena por saldo, de modo que la gestión de cobro no dependa de
    revisar los expedientes uno por uno.
    """
    solo_pendientes = request.GET.get('pendientes', '1') == '1'
    consulta = (PlanTratamiento.objects
                .filter(estado=True, estado_plan__in=PlanTratamiento.ABIERTOS)
                .select_related('paciente', 'odontologo')
                .prefetch_related('detalles', 'pagos'))

    todos = list(consulta)
    if solo_pendientes:
        todos = [p for p in todos if p.saldo > Decimal('0.00')]
    todos.sort(key=lambda p: p.saldo, reverse=True)

    total_por_cobrar = sum((p.saldo for p in todos), Decimal('0.00'))
    cobrado_mes = (Pago.objects
                   .filter(estado=True, fecha__year=timezone.localdate().year,
                           fecha__month=timezone.localdate().month)
                   .aggregate(total=Sum('monto'))['total'] or Decimal('0.00'))

    return render(request, 'clinico/cobros.html', {
        'planes': todos[:200],
        'solo_pendientes': solo_pendientes,
        'total_por_cobrar': total_por_cobrar,
        'cobrado_mes': cobrado_mes,
        'presupuestado': sum((p.total for p in todos), Decimal('0.00')),
    })


@login_required
@escritura_requerida('finanzas')
def anular_pago(request, pk):
    """Anulación lógica de un abono mal registrado."""
    pago = get_object_or_404(Pago, pk=pk)
    plan = pago.plan
    if request.method == 'POST':
        pago.estado = False
        pago.save(update_fields=['estado'])
        HistorialPlan.registrar(plan, 'ANULACION', request.user.username,
                                detalle=f'Abono anulado: Q{pago.monto}')
        messages.success(request, f'Abono de Q{pago.monto} anulado. '
                                  f'Saldo: Q{plan.saldo:.2f}.')
    return redirect('clinico:plan_detalle', pk=plan.pk)

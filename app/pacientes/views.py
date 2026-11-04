"""Módulo de Pacientes: registro, consulta, ficha clínica y antecedentes.

Aplica borrado lógico e historial de auditoría, igual que el módulo de Usuarios.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.decorators import escritura_requerida, modulo_requerido

from .forms import AntecedenteMedicoForm, PacienteForm
from .models import AntecedenteMedico, HistorialPaciente, Paciente


def _auditar(paciente, accion, usuario):
    HistorialPaciente.objects.create(
        paciente_ref=paciente.pk,
        codigo=paciente.codigo,
        nombre_completo=f"{paciente.nombres} {paciente.apellidos}",
        estado_anterior=paciente.estado,
        accion=accion,
        realizado_por=usuario,
    )


@login_required
@modulo_requerido("pacientes")
def lista(request):
    q = request.GET.get("q", "").strip()
    mostrar_inactivos = request.GET.get("inactivos") == "1"

    pacientes = Paciente.objects.all()
    if not mostrar_inactivos:
        pacientes = pacientes.filter(estado=True)
    if q:
        pacientes = pacientes.filter(
            Q(codigo__icontains=q)
            | Q(nombres__icontains=q)
            | Q(apellidos__icontains=q)
            | Q(telefono__icontains=q)
        )

    return render(
        request,
        "pacientes/lista.html",
        {
            "pacientes": pacientes.order_by("apellidos", "nombres")[:200],
            "q": q,
            "mostrar_inactivos": mostrar_inactivos,
            "total_activos": Paciente.objects.filter(estado=True).count(),
        },
    )


@login_required
@escritura_requerida("pacientes")
def crear(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save()
            _auditar(paciente, "CREACION", request.user.username)
            messages.success(
                request, f"Paciente {paciente.codigo} registrado correctamente."
            )
            return redirect("pacientes:ficha", pk=paciente.pk)
    else:
        form = PacienteForm()
    return render(
        request, "pacientes/form.html", {"form": form, "titulo": "Registro de paciente"}
    )


@login_required
@escritura_requerida("pacientes")
def editar(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        # Copia del estado previo para la auditoría: is_valid() ya escribe los
        # datos nuevos en `paciente`.
        previo = Paciente.objects.get(pk=pk)
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            _auditar(previo, "ACTUALIZACION", request.user.username)
            paciente = form.save()
            messages.success(request, "Los datos del paciente fueron actualizados.")
            return redirect("pacientes:ficha", pk=paciente.pk)
    else:
        form = PacienteForm(instance=paciente)
    return render(
        request,
        "pacientes/form.html",
        {
            "form": form,
            "paciente": paciente,
            "titulo": f"Editar paciente: {paciente.nombres} {paciente.apellidos}",
        },
    )


@login_required
@modulo_requerido("pacientes")
def ficha(request, pk):
    """Ficha clínica: datos personales, antecedentes e historial de citas."""
    paciente = get_object_or_404(Paciente, pk=pk)
    citas = (
        paciente.citas.filter(estado=True)
        .select_related("procedimiento", "odontologo")
        .order_by("-fecha", "-hora_inicio_programada")[:30]
    )

    if request.method == "POST":
        form = AntecedenteMedicoForm(request.POST)
        if form.is_valid():
            antecedente = form.save(commit=False)
            antecedente.paciente = paciente
            antecedente.save()
            _auditar(paciente, "ACTUALIZACION", request.user.username)
            messages.success(request, "Antecedente médico agregado a la ficha.")
            return redirect("pacientes:ficha", pk=paciente.pk)
    else:
        form = AntecedenteMedicoForm()

    return render(
        request,
        "pacientes/ficha.html",
        {
            "paciente": paciente,
            "antecedentes": paciente.antecedentes.filter(estado=True).order_by(
                "-creado"
            ),
            "citas": citas,
            "form": form,
            "historial": HistorialPaciente.objects.filter(paciente_ref=paciente.pk)[
                :10
            ],
        },
    )


@login_required
@escritura_requerida("pacientes")
def cambiar_estado(request, pk):
    """Borrado lógico: activa o desactiva sin eliminar físicamente el registro."""
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        _auditar(
            paciente,
            "DESACTIVACION" if paciente.estado else "ACTIVACION",
            request.user.username,
        )
        paciente.estado = not paciente.estado
        paciente.save(update_fields=["estado"])
        estado = "activado" if paciente.estado else "desactivado"
        messages.success(request, f"El paciente {paciente.codigo} fue {estado}.")
    return redirect("pacientes:lista")


@login_required
@escritura_requerida("pacientes")
def quitar_antecedente(request, pk):
    """Borrado lógico de un antecedente médico."""
    antecedente = get_object_or_404(AntecedenteMedico, pk=pk)
    paciente_pk = antecedente.paciente.pk
    if request.method == "POST":
        antecedente.estado = False
        antecedente.save(update_fields=["estado"])
        _auditar(antecedente.paciente, "ACTUALIZACION", request.user.username)
        messages.success(request, "El antecedente fue retirado de la ficha.")
    return redirect("pacientes:ficha", pk=paciente_pk)

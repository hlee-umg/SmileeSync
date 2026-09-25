"""Módulo de Catálogo Odontológico: especialidades, procedimientos y odontólogos.

Las tres entidades comparten el mismo comportamiento (listar, crear, editar y
aplicar borrado lógico), por lo que se resuelven con vistas genéricas
parametrizadas en lugar de repetir el mismo código tres veces.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.decorators import escritura_requerida, modulo_requerido

from .forms import EspecialidadForm, OdontologoForm, ProcedimientoForm
from .models import Especialidad, Odontologo, Procedimiento

# Configuración de cada entidad del catálogo: modelo, formulario y etiquetas.
ENTIDADES = {
    'procedimientos': {
        'modelo': Procedimiento, 'form': ProcedimientoForm,
        'singular': 'procedimiento', 'plural': 'Procedimientos',
        'orden': ['nombre'],
        'busqueda': lambda q: Q(codigo__icontains=q) | Q(nombre__icontains=q),
    },
    'especialidades': {
        'modelo': Especialidad, 'form': EspecialidadForm,
        'singular': 'especialidad', 'plural': 'Especialidades',
        'orden': ['nombre'],
        'busqueda': lambda q: Q(nombre__icontains=q) | Q(descripcion__icontains=q),
    },
    'odontologos': {
        'modelo': Odontologo, 'form': OdontologoForm,
        'singular': 'odontólogo', 'plural': 'Odontólogos',
        'orden': ['apellidos', 'nombres'],
        'busqueda': lambda q: (Q(nombres__icontains=q) | Q(apellidos__icontains=q) |
                               Q(colegiado__icontains=q)),
    },
}


def _config(entidad):
    if entidad not in ENTIDADES:
        from django.http import Http404
        raise Http404('Entidad de catálogo no reconocida.')
    return ENTIDADES[entidad]


@login_required
@modulo_requerido('catalogos')
def lista(request, entidad='procedimientos'):
    cfg = _config(entidad)
    q = request.GET.get('q', '').strip()
    mostrar_inactivos = request.GET.get('inactivos') == '1'

    registros = cfg['modelo'].objects.all()
    if not mostrar_inactivos:
        registros = registros.filter(estado=True)
    if q:
        registros = registros.filter(cfg['busqueda'](q))
    if entidad == 'procedimientos':
        registros = registros.select_related('especialidad')
    elif entidad == 'odontologos':
        # El conteo de franjas activas advierte en la lista a quién no se le
        # pueden programar citas todavía.
        registros = (registros.select_related('especialidad', 'usuario')
                     .annotate(num_horarios=Count(
                         'horarios', filter=Q(horarios__estado=True))))

    return render(request, f'catalogo/{entidad}.html', {
        'registros': registros.order_by(*cfg['orden'])[:200],
        'entidad': entidad, 'q': q, 'mostrar_inactivos': mostrar_inactivos,
        'plural': cfg['plural'], 'singular': cfg['singular'],
    })


@login_required
@escritura_requerida('catalogos')
def crear(request, entidad):
    cfg = _config(entidad)
    if request.method == 'POST':
        form = cfg['form'](request.POST)
        if form.is_valid():
            registro = form.save()
            messages.success(request, f'{cfg["singular"].capitalize()} "{registro}" '
                                      f'registrado correctamente.')
            return redirect('catalogo:lista', entidad=entidad)
    else:
        form = cfg['form']()
    return render(request, 'catalogo/form.html', {
        'form': form, 'entidad': entidad,
        'titulo': f'Nuevo {cfg["singular"]}', 'plural': cfg['plural'],
    })


@login_required
@escritura_requerida('catalogos')
def editar(request, entidad, pk):
    cfg = _config(entidad)
    registro = get_object_or_404(cfg['modelo'], pk=pk)
    if request.method == 'POST':
        form = cfg['form'](request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, f'{cfg["singular"].capitalize()} actualizado correctamente.')
            return redirect('catalogo:lista', entidad=entidad)
    else:
        form = cfg['form'](instance=registro)
    return render(request, 'catalogo/form.html', {
        'form': form, 'entidad': entidad, 'registro': registro,
        'titulo': f'Editar {cfg["singular"]}: {registro}', 'plural': cfg['plural'],
    })


@login_required
@escritura_requerida('catalogos')
def cambiar_estado(request, entidad, pk):
    """Borrado lógico: el registro dado de baja deja de ofrecerse al programar
    una cita, pero conserva su vínculo con las citas históricas."""
    cfg = _config(entidad)
    registro = get_object_or_404(cfg['modelo'], pk=pk)
    if request.method == 'POST':
        registro.estado = not registro.estado
        registro.save(update_fields=['estado'])
        estado = 'activado' if registro.estado else 'desactivado'
        messages.success(request, f'{cfg["singular"].capitalize()} "{registro}" {estado}.')
    return redirect('catalogo:lista', entidad=entidad)

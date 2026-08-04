from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Usuario, HistorialUsuario
from .forms import UsuarioCrearForm, UsuarioEditarForm
from .decorators import modulo_requerido


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


@login_required
@modulo_requerido('usuarios')
def lista(request):
    q = request.GET.get('q', '').strip()
    usuarios = Usuario.objects.select_related('rol').order_by('username')
    if q:
        usuarios = usuarios.filter(username__icontains=q)
    return render(request, 'usuarios/lista.html', {'usuarios': usuarios, 'q': q})


@login_required
@modulo_requerido('usuarios')
def crear(request):
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            HistorialUsuario.registrar(usuario, 'CREACION', request.user.username)
            messages.success(request, f'Usuario "{usuario.username}" creado correctamente.')
            return redirect('usuarios:lista')
    else:
        form = UsuarioCrearForm()
    return render(request, 'usuarios/form.html', {'form': form, 'titulo': 'Nuevo usuario'})


@login_required
@modulo_requerido('usuarios')
def editar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            # Histórico: se registra el estado previo antes de actualizar
            HistorialUsuario.registrar(usuario, 'ACTUALIZACION', request.user.username)
            form.save()
            messages.success(request, f'Usuario "{usuario.username}" actualizado.')
            return redirect('usuarios:lista')
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(request, 'usuarios/form.html',
                  {'form': form, 'titulo': f'Editar usuario: {usuario.username}'})


@login_required
@modulo_requerido('usuarios')
def cambiar_estado(request, pk):
    """Borrado lógico: activa/desactiva sin eliminar físicamente.
    Registra el cambio en la tabla de histórico."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        if usuario == request.user:
            messages.error(request, 'No puede desactivar su propia cuenta.')
            return redirect('usuarios:lista')
        HistorialUsuario.registrar(
            usuario, 'DESACTIVACION' if usuario.estado else 'ACTIVACION',
            request.user.username)
        usuario.estado = not usuario.estado
        usuario.is_active = usuario.estado  # impide iniciar sesión si está inactivo
        usuario.save(update_fields=['estado', 'is_active'])
        estado_txt = 'activado' if usuario.estado else 'desactivado'
        messages.success(request, f'Usuario "{usuario.username}" {estado_txt}.')
    return redirect('usuarios:lista')


@login_required
@modulo_requerido('usuarios')
def historial(request):
    registros = HistorialUsuario.objects.all()[:200]
    return render(request, 'usuarios/historial.html', {'registros': registros})

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Usuario, HistorialUsuario
from .forms import UsuarioCrearForm, UsuarioEditarForm
from .decorators import escritura_requerida, modulo_requerido


@login_required
@modulo_requerido("usuarios")
def lista(request):
    q = request.GET.get("q", "").strip()
    usuarios = Usuario.objects.select_related("rol").order_by("username")
    if q:
        usuarios = usuarios.filter(username__icontains=q)
    return render(request, "usuarios/lista.html", {"usuarios": usuarios, "q": q})


@login_required
@escritura_requerida("usuarios")
def crear(request):
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            HistorialUsuario.registrar(usuario, "CREACION", request.user.username)
            messages.success(
                request, f'Usuario "{usuario.username}" creado correctamente.'
            )
            return redirect("usuarios:lista")
    else:
        form = UsuarioCrearForm()
    return render(
        request, "usuarios/form.html", {"form": form, "titulo": "Nuevo usuario"}
    )


@login_required
@escritura_requerida("usuarios")
def editar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == "POST":
        # Histórico: se registra el estado previo. Se toma una copia aparte
        # porque is_valid() ya escribe los datos nuevos en `usuario`.
        previo = Usuario.objects.select_related("rol").get(pk=pk)
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            HistorialUsuario.registrar(previo, "ACTUALIZACION", request.user.username)
            form.save()
            messages.success(request, f'Usuario "{usuario.username}" actualizado.')
            return redirect("usuarios:lista")
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(
        request,
        "usuarios/form.html",
        {"form": form, "titulo": f"Editar usuario: {usuario.username}"},
    )


@login_required
@escritura_requerida("usuarios")
def cambiar_estado(request, pk):
    """Borrado lógico: activa/desactiva sin eliminar físicamente.
    Registra el cambio en la tabla de histórico."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == "POST":
        if usuario == request.user:
            messages.error(request, "No puede desactivar su propia cuenta.")
            return redirect("usuarios:lista")
        HistorialUsuario.registrar(
            usuario,
            "DESACTIVACION" if usuario.estado else "ACTIVACION",
            request.user.username,
        )
        usuario.estado = not usuario.estado
        usuario.is_active = usuario.estado  # impide iniciar sesión si está inactivo
        usuario.save(update_fields=["estado", "is_active"])
        estado_txt = "activado" if usuario.estado else "desactivado"
        messages.success(request, f'Usuario "{usuario.username}" {estado_txt}.')
    return redirect("usuarios:lista")


@login_required
@modulo_requerido("usuarios")
def historial(request):
    registros = HistorialUsuario.objects.all()[:200]
    return render(request, "usuarios/historial.html", {"registros": registros})


# ================= Recuperación de contraseña (pregunta secreta) =================
from .models import Usuario
from .forms import RecuperarCorreoForm, RecuperarRespuestaForm, NuevaPasswordForm


def recuperar_correo(request):
    """Paso 1: el usuario ingresa su correo."""
    if request.method == "POST":
        form = RecuperarCorreoForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            usuario = Usuario.objects.filter(email__iexact=email).first()
            if usuario and usuario.pregunta_secreta and usuario.respuesta_secreta:
                request.session["recuperar_uid"] = usuario.pk
                request.session.pop("recuperar_ok", None)
                return redirect("usuarios:recuperar_pregunta")
            form.add_error(
                "email",
                "No se encontró una cuenta con pregunta secreta configurada para ese correo.",
            )
    else:
        form = RecuperarCorreoForm()
    return render(request, "registration/recuperar_correo.html", {"form": form})


def recuperar_pregunta(request):
    """Paso 2: se muestra la pregunta secreta y se valida la respuesta."""
    uid = request.session.get("recuperar_uid")
    usuario = Usuario.objects.filter(pk=uid).first() if uid else None
    if not usuario:
        return redirect("usuarios:recuperar_correo")
    pregunta = usuario.get_pregunta_secreta_display()
    if request.method == "POST":
        form = RecuperarRespuestaForm(request.POST)
        if form.is_valid():
            if usuario.check_respuesta_secreta(form.cleaned_data["respuesta"]):
                request.session["recuperar_ok"] = True
                return redirect("usuarios:recuperar_nueva")
            form.add_error("respuesta", "La respuesta no es correcta.")
    else:
        form = RecuperarRespuestaForm()
    return render(
        request,
        "registration/recuperar_pregunta.html",
        {"form": form, "pregunta": pregunta},
    )


def recuperar_nueva(request):
    """Paso 3: define la nueva contraseña (solo si respondió correctamente)."""
    uid = request.session.get("recuperar_uid")
    if not uid or not request.session.get("recuperar_ok"):
        return redirect("usuarios:recuperar_correo")
    usuario = Usuario.objects.filter(pk=uid).first()
    if not usuario:
        return redirect("usuarios:recuperar_correo")
    if request.method == "POST":
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data["password1"])
            usuario.save(update_fields=["password"])
            request.session.pop("recuperar_uid", None)
            request.session.pop("recuperar_ok", None)
            messages.success(
                request, "Tu contraseña fue restablecida. Ya puedes iniciar sesión."
            )
            return redirect("login")
    else:
        form = NuevaPasswordForm()
    return render(request, "registration/recuperar_nueva.html", {"form": form})

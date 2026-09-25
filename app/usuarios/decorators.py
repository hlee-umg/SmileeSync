from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def modulo_requerido(modulo):
    """Restringe una vista a los usuarios cuyo rol tiene acceso al módulo."""
    def decorador(vista):
        @wraps(vista)
        def _envuelta(request, *args, **kwargs):
            u = request.user
            if not u.is_authenticated:
                return redirect('login')
            if u.puede(modulo):
                return vista(request, *args, **kwargs)
            raise PermissionDenied('No tiene acceso a este módulo.')
        return _envuelta
    return decorador


def escritura_requerida(modulo):
    """Restringe una vista que modifica información.

    Exige acceso al módulo y, además, que el rol no sea de solo consulta. Se
    aplica a las vistas de alta, edición, cambio de estado y registro de
    tiempos, de modo que la restricción no dependa de ocultar el botón en la
    plantilla: el acceso directo a la dirección también queda denegado.
    """
    def decorador(vista):
        @wraps(vista)
        def _envuelta(request, *args, **kwargs):
            u = request.user
            if not u.is_authenticated:
                return redirect('login')
            if not u.puede(modulo):
                raise PermissionDenied('No tiene acceso a este módulo.')
            if u.es_solo_consulta:
                raise PermissionDenied(
                    'Su rol es de solo consulta: no puede modificar información.')
            return vista(request, *args, **kwargs)
        return _envuelta
    return decorador


def puede_gestionar_odontologo(usuario, odontologo):
    """Si el usuario puede administrar la disponibilidad de ese odontólogo.

    Además de quien tiene escritura en la agenda, se permite al propio
    odontólogo sobre su ficha: su rol es de solo consulta para la agenda de la
    clínica, pero marcar sus ausencias es información suya. Es el único caso en
    que un rol de consulta escribe, y está acotado a sus propios registros.
    """
    if usuario.puede_escribir('agenda'):
        return True
    return bool(odontologo and odontologo.usuario_id == usuario.pk)

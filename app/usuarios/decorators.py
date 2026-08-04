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

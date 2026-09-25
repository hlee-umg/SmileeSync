"""Contexto de permisos disponible en todas las plantillas.

Permite escribir en las plantillas condiciones como {% if escritura.agenda %}
para ocultar los botones de acción a los roles de solo consulta. La seguridad
efectiva la aplica el decorador `escritura_requerida`; esto es solo interfaz.
"""
MODULOS = ['usuarios', 'pacientes', 'catalogos', 'agenda', 'inteligencia', 'reportes']


def permisos(request):
    usuario = getattr(request, 'user', None)
    if usuario is None or not usuario.is_authenticated:
        return {'escritura': {}, 'solo_consulta': False}
    return {
        'escritura': {m: usuario.puede_escribir(m) for m in MODULOS},
        'solo_consulta': usuario.es_solo_consulta,
    }

from django.conf import settings


class NoCacheMiddleware:
    """Evita que el navegador guarde en caché las páginas dinámicas.

    Sin esto, tras cerrar sesión el botón 'Atrás' del navegador puede mostrar
    una página autenticada desde la caché (aunque la sesión ya no exista).
    Con estos encabezados, el navegador vuelve a solicitar la página al servidor,
    que redirige al login si no hay sesión.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # No aplicar a archivos estáticos (deben poder cachearse).
        if not request.path.startswith(settings.STATIC_URL):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response

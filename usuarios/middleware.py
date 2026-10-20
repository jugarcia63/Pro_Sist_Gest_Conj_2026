from django.shortcuts import redirect

RUTAS_PERMITIDAS_SIN_CAMBIO = ('cambiar_password', 'password_change_done', 'logout', 'login', 'set_language')


class ForzarCambioPasswordMiddleware:
    """Si el usuario tiene una contraseña temporal pendiente (debe_cambiar_password),
    lo obliga a pasar por 'Cambiar contraseña' antes de usar cualquier otra página.

    La revisión se hace en process_view y no en __call__: en __call__ Django todavía
    no ha resuelto la URL, así que request.resolver_match aún no existe."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        usuario = getattr(request, 'user', None)
        if (
            usuario is not None
            and usuario.is_authenticated
            and getattr(usuario, 'debe_cambiar_password', False)
            and request.resolver_match.url_name not in RUTAS_PERMITIDAS_SIN_CAMBIO
        ):
            return redirect('cambiar_password')
        return None

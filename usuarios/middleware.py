from django.shortcuts import redirect
from django.urls import reverse

RUTAS_PERMITIDAS_SIN_CAMBIO = ('cambiar_password', 'password_change_done', 'logout')


class ForzarCambioPasswordMiddleware:
    """Si el usuario tiene una contraseña temporal pendiente (debe_cambiar_password),
    lo obliga a pasar por 'Cambiar contraseña' antes de usar cualquier otra página."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, 'user', None)
        if (
            usuario is not None
            and usuario.is_authenticated
            and getattr(usuario, 'debe_cambiar_password', False)
            and request.resolver_match
            and request.resolver_match.url_name not in RUTAS_PERMITIDAS_SIN_CAMBIO
        ):
            return redirect(reverse('cambiar_password'))
        return self.get_response(request)

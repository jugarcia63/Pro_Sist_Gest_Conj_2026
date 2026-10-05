"""
Control de acceso por rol, reutilizable en las demás apps.

Uso en vistas basadas en función:
    @rol_requerido('admin')
    def mi_vista(request): ...

Uso en vistas basadas en clase (ListView, CreateView, UpdateView, ...):
    class MiVista(RolRequeridoMixin, ListView):
        roles_permitidos = ('admin', 'seguridad')
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles):
    def decorador(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.rol not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorador


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige sesión iniciada y que request.user.rol esté en roles_permitidos."""
    roles_permitidos = ()

    def test_func(self):
        return self.request.user.rol in self.roles_permitidos


def residente_de(usuario):
    """Devuelve el registro Residentes vinculado a este Usuario, o None si no tiene."""
    return getattr(usuario, 'residente', None)

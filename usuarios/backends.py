from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsuarioSinMayusculasBackend(ModelBackend):
    """Igual al backend estándar, pero el nombre de usuario no distingue mayúsculas y minúsculas."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        Usuario = get_user_model()
        if username is None:
            username = kwargs.get(Usuario.USERNAME_FIELD)
        if username is None or password is None:
            return None
        usuario = Usuario.objects.filter(username__iexact=username.strip()).order_by('id').first()
        if usuario is None:
            Usuario().set_password(password)  # mismo tiempo de respuesta que con un usuario real
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None

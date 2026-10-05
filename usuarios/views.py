from django.shortcuts import render
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.decorators import login_required


class MiLoginView(LoginView):
    template_name = 'usuarios/login.html'


class CambiarPasswordView(PasswordChangeView):
    """Igual al PasswordChangeView estándar, pero además apaga la bandera
    de 'contraseña temporal pendiente de cambiar' cuando el cambio tiene éxito."""
    template_name = 'usuarios/cambiar_password.html'
    success_url = '/cambiar-password/hecho/'

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.debe_cambiar_password = False
        self.request.user.save(update_fields=['debe_cambiar_password'])
        return response


@login_required
def dashboard(request):
    rol = request.user.rol
    if rol == 'admin':
        template = 'usuarios/dashboard_admin.html'
    elif rol == 'seguridad':
        template = 'usuarios/dashboard_seguridad.html'
    else:
        template = 'usuarios/dashboard_residente.html'
    return render(request, template, {'usuario': request.user})
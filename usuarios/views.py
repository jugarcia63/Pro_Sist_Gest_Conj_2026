from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required


class MiLoginView(LoginView):
    template_name = 'usuarios/login.html'


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
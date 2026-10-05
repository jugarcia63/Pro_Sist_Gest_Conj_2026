from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.crypto import get_random_string
from usuarios.models import Usuario
from usuarios.permisos import rol_requerido, RolRequeridoMixin
from .models import Residentes
from .forms import ResidenteForm


class ListaResidentes(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin',)
    model = Residentes
    template_name = 'residentes/lista_residentes.html'
    context_object_name = 'residentes'

    def get_queryset(self):
        queryset = super().get_queryset()
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(nombres__icontains=buscar)
        return queryset


def _crear_usuario_login(residente, request):
    """Crea la cuenta de login del residente (o la vincula si ya existía) y muestra la contraseña temporal."""
    if not residente.email:
        messages.warning(request, 'Residente guardado, pero sin email no se pudo generar su cuenta de acceso.')
        return

    if residente.usuario_id:
        return  # ya tiene una cuenta vinculada, no se toca

    usuario_existente = Usuario.objects.filter(email__iexact=residente.email).first()
    if usuario_existente:
        residente.usuario = usuario_existente
        residente.save(update_fields=['usuario'])
        return

    username_base = residente.email.split('@')[0]
    username = username_base
    contador = 1
    while Usuario.objects.filter(username__iexact=username).exists():
        username = f"{username_base}{contador}"
        contador += 1

    password_temporal = get_random_string(8)
    usuario = Usuario.objects.create_user(username=username, email=residente.email, password=password_temporal)
    usuario.rol = 'residente'
    usuario.debe_cambiar_password = True
    usuario.save()

    residente.usuario = usuario
    residente.save(update_fields=['usuario'])

    messages.success(
        request,
        f'Residente creado. Credenciales — Usuario: "{username}" / Contraseña temporal: "{password_temporal}" (compártela con el residente).'
    )


class CrearResidente(RolRequeridoMixin, CreateView):
    roles_permitidos = ('admin',)
    model = Residentes
    form_class = ResidenteForm
    template_name = 'residentes/form_residente.html'
    success_url = reverse_lazy('lista_residentes')

    def form_valid(self, form):
        response = super().form_valid(form)
        _crear_usuario_login(self.object, self.request)
        return response


class EditarResidente(RolRequeridoMixin, UpdateView):
    roles_permitidos = ('admin',)
    model = Residentes
    form_class = ResidenteForm
    template_name = 'residentes/form_residente.html'
    success_url = reverse_lazy('lista_residentes')
    pk_url_kwarg = 'id_residente'


@rol_requerido('admin')
def eliminar_residente(request, id_residente):
    residente = get_object_or_404(Residentes, pk=id_residente)

    if request.method == 'POST':
        from pagos.models import Pago
        from reportes.models import ReporteDano
        from vehiculos.models import Vehiculos
        from visitantes.models import Visitantes

        nombre = f"{residente.nombres} {residente.apellidos}"

        # Borra en cascada manual todo lo que depende de este residente
        Pago.objects.filter(id_residente_fk=residente).delete()
        ReporteDano.objects.filter(id_residente_fk=residente).delete()
        Vehiculos.objects.filter(id_residente_fk=residente).delete()
        Visitantes.objects.filter(id_residente_fk=residente).delete()

        if residente.usuario_id:
            residente.usuario.delete()
        residente.delete()
        messages.success(request, f'Residente "{nombre}" y sus registros asociados fueron eliminados.')

    return redirect('lista_residentes')


@rol_requerido('admin')
def resetear_password(request, id_residente):
    residente = get_object_or_404(Residentes, pk=id_residente)
    usuario = residente.usuario

    if not usuario:
        messages.error(request, 'Este residente no tiene una cuenta de acceso asociada.')
        return redirect('lista_residentes')

    if request.method == 'POST':
        nueva_password = get_random_string(8)
        usuario.set_password(nueva_password)
        usuario.debe_cambiar_password = True
        usuario.save()
        messages.success(
            request,
            f'Contraseña reseteada para {usuario.username}. Nueva contraseña temporal: "{nueva_password}" (compártela con el residente).'
        )

    return redirect('lista_residentes')
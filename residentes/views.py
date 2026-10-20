from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from .forms import ResidenteForm, UnidadForm
from .models import Residentes, Unidades


class ListaResidentes(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin',)
    model = Residentes
    template_name = 'residentes/lista_residentes.html'
    context_object_name = 'residentes'
    paginate_by = 15

    def get_queryset(self):
        queryset = Residentes.objects.select_related('id_unidad_fk', 'usuario').order_by('nombres', 'apellidos')
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(
                Q(nombres__icontains=buscar) | Q(apellidos__icontains=buscar)
                | Q(num_documento__icontains=buscar) | Q(email__icontains=buscar)
            )
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['buscar'] = self.request.GET.get('buscar', '')
        contexto['total'] = Residentes.objects.count()
        contexto['con_cuenta'] = Residentes.objects.filter(usuario__isnull=False).count()
        contexto['sin_unidad'] = Residentes.objects.filter(id_unidad_fk__isnull=True).count()
        return contexto


def _sincronizar_correo(residente):
    """Si el residente ya tiene cuenta, su correo se mantiene igual al del registro."""
    if residente.usuario_id and residente.email and residente.usuario.email != residente.email:
        residente.usuario.email = residente.email
        residente.usuario.save(update_fields=['email'])


class CrearResidente(RolRequeridoMixin, CreateView):
    roles_permitidos = ('admin',)
    model = Residentes
    form_class = ResidenteForm
    template_name = 'residentes/form_residente.html'
    success_url = reverse_lazy('lista_residentes')

    def form_valid(self, form):
        form.instance.fecha_registro = timezone.now()
        form.instance.estado = 1
        response = super().form_valid(form)
        messages.success(self.request, _('Residente "%(nombre)s" registrado. Ya puede crear su cuenta en '
                                         '"Registrarse" con su número de documento.') % {'nombre': self.object})
        return response


class EditarResidente(RolRequeridoMixin, UpdateView):
    roles_permitidos = ('admin',)
    model = Residentes
    form_class = ResidenteForm
    template_name = 'residentes/form_residente.html'
    success_url = reverse_lazy('lista_residentes')
    pk_url_kwarg = 'id_residente'

    def form_valid(self, form):
        response = super().form_valid(form)
        _sincronizar_correo(self.object)
        messages.success(self.request, _('Datos de "%(nombre)s" actualizados.') % {'nombre': self.object})
        return response


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

        usuario = residente.usuario
        residente.delete()
        # Solo se borra la cuenta si es de residente (nunca una cuenta de admin o seguridad)
        if usuario and usuario.rol == 'residente':
            usuario.delete()
        messages.success(request, _('Residente "%(nombre)s" y sus registros asociados fueron eliminados.')
                         % {'nombre': nombre})

    return redirect('lista_residentes')


# ---------- Unidades (torres y apartamentos) ----------

class ListaUnidades(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin',)
    model = Unidades
    template_name = 'residentes/lista_unidades.html'
    context_object_name = 'unidades'
    paginate_by = 20

    def get_queryset(self):
        queryset = Unidades.objects.annotate(num_residentes=Count('residentes')).order_by('torre', 'piso', 'apto')
        torre = self.request.GET.get('torre', '').strip()
        if torre:
            queryset = queryset.filter(torre__iexact=torre)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['torres'] = (Unidades.objects.exclude(torre__isnull=True).exclude(torre='')
                              .order_by('torre').values_list('torre', flat=True).distinct())
        contexto['torre_actual'] = self.request.GET.get('torre', '')
        return contexto


class CrearUnidad(RolRequeridoMixin, CreateView):
    roles_permitidos = ('admin',)
    model = Unidades
    form_class = UnidadForm
    template_name = 'residentes/form_unidad.html'
    success_url = reverse_lazy('lista_unidades')

    def form_valid(self, form):
        messages.success(self.request, _('Unidad creada.'))
        return super().form_valid(form)


class EditarUnidad(RolRequeridoMixin, UpdateView):
    roles_permitidos = ('admin',)
    model = Unidades
    form_class = UnidadForm
    template_name = 'residentes/form_unidad.html'
    success_url = reverse_lazy('lista_unidades')
    pk_url_kwarg = 'id_unidad'

    def form_valid(self, form):
        messages.success(self.request, _('Unidad actualizada.'))
        return super().form_valid(form)


@rol_requerido('admin')
def eliminar_unidad(request, id_unidad):
    unidad = get_object_or_404(Unidades, pk=id_unidad)
    if request.method == 'POST':
        from reservas.models import Reservas
        if Residentes.objects.filter(id_unidad_fk=unidad).exists() or Reservas.objects.filter(id_unidad_fk=unidad).exists():
            messages.error(request, _('No se puede eliminar %(unidad)s: tiene residentes o reservas asociadas.')
                           % {'unidad': unidad})
        else:
            unidad.delete()
            messages.success(request, _('%(unidad)s eliminada.') % {'unidad': unidad})
    return redirect('lista_unidades')

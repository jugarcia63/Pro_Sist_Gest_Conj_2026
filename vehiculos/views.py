from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin, residente_de, rol_requerido
from .forms import VehiculoForm
from .models import Vehiculos
from django.utils.translation import gettext as _


def _vehiculos_visibles(usuario):
    """Residente: solo sus vehículos. Admin y seguridad: todos."""
    queryset = Vehiculos.objects.select_related('id_residente_fk__id_unidad_fk').order_by('placa')
    if usuario.rol == 'residente':
        residente = residente_de(usuario)
        return queryset.filter(id_residente_fk=residente) if residente else queryset.none()
    return queryset


class ListaVehiculos(RolRequeridoMixin, ListView):
    """Seguridad consulta todos en modo solo lectura."""
    roles_permitidos = ('admin', 'seguridad', 'residente')
    template_name = 'vehiculos/lista_vehiculos.html'
    context_object_name = 'vehiculos'
    paginate_by = 15

    def get_queryset(self):
        queryset = _vehiculos_visibles(self.request.user)
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(
                Q(placa__icontains=buscar.replace(' ', '')) | Q(marca__icontains=buscar)
                | Q(id_residente_fk__nombres__icontains=buscar) | Q(id_residente_fk__apellidos__icontains=buscar)
            )
        tipo = self.request.GET.get('tipo', '')
        if tipo in ('Carro', 'Moto'):
            queryset = queryset.filter(tipo_vehiculo=tipo)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        todos = _vehiculos_visibles(self.request.user)
        contexto.update({
            'buscar': self.request.GET.get('buscar', ''),
            'tipo': self.request.GET.get('tipo', ''),
            'total_carros': todos.filter(tipo_vehiculo='Carro').count(),
            'total_motos': todos.filter(tipo_vehiculo='Moto').count(),
            'puede_editar': self.request.user.rol in ('admin', 'residente'),
        })
        return contexto


class VehiculoFormMixin:
    roles_permitidos = ('admin', 'residente')
    model = Vehiculos
    form_class = VehiculoForm
    template_name = 'vehiculos/form_vehiculo.html'
    success_url = reverse_lazy('lista_vehiculos')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol == 'residente' and not residente_de(request.user):
            messages.error(request, _('Tu usuario no está vinculado a un residente. Pide al administrador que lo vincule.'))
            return redirect('lista_vehiculos')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['es_residente'] = self.request.user.rol == 'residente'
        return kwargs

    def form_valid(self, form):
        if self.request.user.rol == 'residente':
            form.instance.id_residente_fk = residente_de(self.request.user)
        messages.success(self.request, _('Vehículo %(placa)s guardado.') % {'placa': form.instance.placa})
        return super().form_valid(form)


class CrearVehiculo(VehiculoFormMixin, RolRequeridoMixin, CreateView):
    pass


class EditarVehiculo(VehiculoFormMixin, RolRequeridoMixin, UpdateView):
    pk_url_kwarg = 'id_vehiculo'

    def get_queryset(self):
        return _vehiculos_visibles(self.request.user)


@rol_requerido('admin', 'residente')
def eliminar_vehiculo(request, id_vehiculo):
    vehiculo = get_object_or_404(_vehiculos_visibles(request.user), pk=id_vehiculo)
    if request.method == 'POST':
        placa = vehiculo.placa
        vehiculo.delete()
        messages.success(request, _('Vehículo %(placa)s eliminado.') % {'placa': placa})
    return redirect('lista_vehiculos')

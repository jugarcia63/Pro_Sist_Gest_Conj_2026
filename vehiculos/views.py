from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from usuarios.permisos import RolRequeridoMixin, residente_de
from .models import Vehiculos
from .forms import VehiculoForm


class ListaVehiculos(RolRequeridoMixin, ListView):
    """Residente: solo sus vehículos. Seguridad: consulta de todos (solo lectura). Admin: todos."""
    roles_permitidos = ('admin', 'seguridad', 'residente')
    model = Vehiculos
    template_name = 'vehiculos/lista_vehiculos.html'
    context_object_name = 'vehiculos'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            queryset = queryset.filter(id_residente_fk=residente) if residente else queryset.none()
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(placa__icontains=buscar)
        return queryset


class CrearVehiculo(RolRequeridoMixin, CreateView):
    """Un residente solo puede registrar vehículos a su propio nombre; el admin puede elegir cualquiera."""
    roles_permitidos = ('admin', 'residente')
    model = Vehiculos
    form_class = VehiculoForm
    template_name = 'vehiculos/form_vehiculo.html'
    success_url = reverse_lazy('lista_vehiculos')

    def form_valid(self, form):
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            if not residente:
                raise PermissionDenied
            form.instance.id_residente_fk = residente
        return super().form_valid(form)


class EditarVehiculo(RolRequeridoMixin, UpdateView):
    roles_permitidos = ('admin', 'residente')
    model = Vehiculos
    form_class = VehiculoForm
    template_name = 'vehiculos/form_vehiculo.html'
    success_url = reverse_lazy('lista_vehiculos')
    pk_url_kwarg = 'id_vehiculo'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            queryset = queryset.filter(id_residente_fk=residente) if residente else queryset.none()
        return queryset

    def form_valid(self, form):
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            if not residente:
                raise PermissionDenied
            form.instance.id_residente_fk = residente
        return super().form_valid(form)

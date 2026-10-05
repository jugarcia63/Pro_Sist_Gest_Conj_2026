from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from usuarios.permisos import RolRequeridoMixin, residente_de
from .models import Reservas, ZonasComunes
from .forms import ReservaForm


class ListaZonas(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin', 'residente')
    model = ZonasComunes
    template_name = 'reservas/lista_zonas.html'
    context_object_name = 'zonas'


class ListaReservas(RolRequeridoMixin, ListView):
    """Residente: solo las reservas de su propia unidad. Admin: todas."""
    roles_permitidos = ('admin', 'residente')
    model = Reservas
    template_name = 'reservas/lista_reservas.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            queryset = queryset.filter(id_unidad_fk=residente.id_unidad_fk) if residente else queryset.none()
        return queryset


class CrearReserva(RolRequeridoMixin, CreateView):
    """Un residente solo puede reservar para su propia unidad; el admin puede elegir cualquiera."""
    roles_permitidos = ('admin', 'residente')
    model = Reservas
    form_class = ReservaForm
    template_name = 'reservas/form_reserva.html'
    success_url = reverse_lazy('lista_reservas')

    def form_valid(self, form):
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            if not residente or not residente.id_unidad_fk:
                raise PermissionDenied
            form.instance.id_unidad_fk = residente.id_unidad_fk
        return super().form_valid(form)


class EditarReserva(RolRequeridoMixin, UpdateView):
    roles_permitidos = ('admin', 'residente')
    model = Reservas
    form_class = ReservaForm
    template_name = 'reservas/form_reserva.html'
    success_url = reverse_lazy('lista_reservas')
    pk_url_kwarg = 'id_reservas'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            queryset = queryset.filter(id_unidad_fk=residente.id_unidad_fk) if residente else queryset.none()
        return queryset

    def form_valid(self, form):
        if self.request.user.rol == 'residente':
            residente = residente_de(self.request.user)
            if not residente or not residente.id_unidad_fk:
                raise PermissionDenied
            form.instance.id_unidad_fk = residente.id_unidad_fk
        return super().form_valid(form)

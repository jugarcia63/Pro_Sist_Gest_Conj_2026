from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Vehiculos
from .forms import VehiculoForm


class ListaVehiculos(ListView):
    model = Vehiculos
    template_name = 'vehiculos/lista_vehiculos.html'
    context_object_name = 'vehiculos'

    def get_queryset(self):
        queryset = super().get_queryset()
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(placa__icontains=buscar)
        return queryset


class CrearVehiculo(CreateView):
    model = Vehiculos
    form_class = VehiculoForm
    template_name = 'vehiculos/form_vehiculo.html'
    success_url = reverse_lazy('lista_vehiculos')


class EditarVehiculo(UpdateView):
    model = Vehiculos
    form_class = VehiculoForm
    template_name = 'vehiculos/form_vehiculo.html'
    success_url = reverse_lazy('lista_vehiculos')
    pk_url_kwarg = 'id_vehiculo'
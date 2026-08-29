from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Reservas, ZonasComunes
from .forms import ReservaForm


class ListaZonas(ListView):
    model = ZonasComunes
    template_name = 'reservas/lista_zonas.html'
    context_object_name = 'zonas'


class ListaReservas(ListView):
    model = Reservas
    template_name = 'reservas/lista_reservas.html'
    context_object_name = 'reservas'


class CrearReserva(CreateView):
    model = Reservas
    form_class = ReservaForm
    template_name = 'reservas/form_reserva.html'
    success_url = reverse_lazy('lista_reservas')


class EditarReserva(UpdateView):
    model = Reservas
    form_class = ReservaForm
    template_name = 'reservas/form_reserva.html'
    success_url = reverse_lazy('lista_reservas')
    pk_url_kwarg = 'id_reservas'

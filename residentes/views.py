from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Residentes
from .forms import ResidenteForm


class ListaResidentes(ListView):
    model = Residentes
    template_name = 'residentes/lista_residentes.html'
    context_object_name = 'residentes'

    def get_queryset(self):
        queryset = super().get_queryset()
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(nombres__icontains=buscar)
        return queryset


class CrearResidente(CreateView):
    model = Residentes
    form_class = ResidenteForm
    template_name = 'residentes/form_residente.html'
    success_url = reverse_lazy('lista_residentes')


class EditarResidente(UpdateView):
    model = Residentes
    form_class = ResidenteForm
    template_name = 'residentes/form_residente.html'
    success_url = reverse_lazy('lista_residentes')
    pk_url_kwarg = 'id_residente'

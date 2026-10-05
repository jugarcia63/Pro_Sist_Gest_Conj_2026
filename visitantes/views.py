from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from usuarios.permisos import RolRequeridoMixin
from .models import Visitantes
from .forms import VisitanteForm


class ListaVisitantes(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin', 'seguridad')
    model = Visitantes
    template_name = 'visitantes/lista_visitantes.html'
    context_object_name = 'visitantes'

    def get_queryset(self):
        queryset = super().get_queryset()
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(nombre__icontains=buscar)
        return queryset


class CrearVisitante(RolRequeridoMixin, CreateView):
    roles_permitidos = ('admin', 'seguridad')
    model = Visitantes
    form_class = VisitanteForm
    template_name = 'visitantes/form_visitante.html'
    success_url = reverse_lazy('lista_visitantes')


class EditarVisitante(RolRequeridoMixin, UpdateView):
    roles_permitidos = ('admin', 'seguridad')
    model = Visitantes
    form_class = VisitanteForm
    template_name = 'visitantes/form_visitante.html'
    success_url = reverse_lazy('lista_visitantes')
    pk_url_kwarg = 'id_visitante'

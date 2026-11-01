from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin
from .forms import VisitanteForm
from .models import Visitantes


class ListaVisitantes(RolRequeridoMixin, ListView):
    """Bitácora de ingresos. No se registra la salida de las personas."""
    roles_permitidos = ('admin', 'seguridad')
    template_name = 'visitantes/lista_visitantes.html'
    context_object_name = 'visitantes'
    paginate_by = 15

    def get_queryset(self):
        queryset = (Visitantes.objects
                    .select_related('id_unidad_fk', 'id_residente_fk__id_unidad_fk', 'autorizado_por')
                    .order_by('-fecha_ingreso'))
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) | Q(apellidos__icontains=buscar) | Q(num_documento__icontains=buscar)
            )
        if self.request.GET.get('cuando') == 'hoy':
            queryset = queryset.filter(fecha_ingreso__date=timezone.localdate())
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update({
            'buscar': self.request.GET.get('buscar', ''),
            'cuando': self.request.GET.get('cuando', ''),
            'ingresos_hoy': Visitantes.objects.filter(fecha_ingreso__date=timezone.localdate()).count(),
        })
        return contexto


class CrearVisitante(RolRequeridoMixin, CreateView):
    roles_permitidos = ('admin', 'seguridad')
    model = Visitantes
    form_class = VisitanteForm
    template_name = 'visitantes/form_visitante.html'
    success_url = reverse_lazy('lista_visitantes')

    def form_valid(self, form):
        # Queda registrado qué usuario (vigilante o admin) autorizó la entrada
        form.instance.autorizado_por = self.request.user
        form.instance.tipo_documento = 'CC'
        messages.success(self.request, _('Ingreso de %(nombre)s registrado.') % {'nombre': f'{form.instance.nombre} {form.instance.apellidos}'})
        return super().form_valid(form)


class EditarVisitante(RolRequeridoMixin, UpdateView):
    roles_permitidos = ('admin', 'seguridad')
    model = Visitantes
    form_class = VisitanteForm
    template_name = 'visitantes/form_visitante.html'
    success_url = reverse_lazy('lista_visitantes')
    pk_url_kwarg = 'id_visitante'

    def form_valid(self, form):
        messages.success(self.request, _('Registro de visitante actualizado.'))
        return super().form_valid(form)

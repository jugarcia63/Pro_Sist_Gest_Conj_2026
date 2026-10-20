from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin, redirigir_a_siguiente, rol_requerido
from .forms import VisitanteForm
from .models import Visitantes
from django.utils.translation import gettext as _


class ListaVisitantes(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin', 'seguridad')
    template_name = 'visitantes/lista_visitantes.html'
    context_object_name = 'visitantes'
    paginate_by = 15

    def get_queryset(self):
        queryset = (Visitantes.objects
                    .select_related('id_residente_fk__id_unidad_fk', 'autorizado_por')
                    .order_by('-fecha_ingreso'))
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) | Q(apellidos__icontains=buscar) | Q(num_documento__icontains=buscar)
            )
        estado = self.request.GET.get('estado', '')
        if estado in ('Dentro', 'Salió'):
            queryset = queryset.filter(estado=estado)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        contexto.update({
            'buscar': self.request.GET.get('buscar', ''),
            'estado': self.request.GET.get('estado', ''),
            'total_dentro': Visitantes.objects.filter(estado='Dentro').count(),
            'ingresos_hoy': Visitantes.objects.filter(fecha_ingreso__date=hoy).count(),
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


@rol_requerido('admin', 'seguridad')
def registrar_salida(request, id_visitante):
    visitante = get_object_or_404(Visitantes, pk=id_visitante)
    if request.method == 'POST':
        if visitante.estado == 'Salió':
            messages.info(request, _('%(nombre)s ya tenía registrada su salida.') % {'nombre': visitante})
        else:
            visitante.estado = 'Salió'
            visitante.fecha_salida = timezone.now()
            visitante.save(update_fields=['estado', 'fecha_salida'])
            messages.success(request, _('Salida de %(nombre)s registrada a las %(hora)s.') % {'nombre': visitante, 'hora': f'{timezone.localtime():%H:%M}'})

    return redirigir_a_siguiente(request, 'lista_visitantes')

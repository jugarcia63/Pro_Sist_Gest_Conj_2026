from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView

from usuarios.permisos import RolRequeridoMixin, redirigir_a_siguiente, residente_de, rol_requerido
from .forms import CATEGORIAS, ReporteDanoForm
from .models import ReporteDano
from django.utils.translation import gettext as _

ESTADOS_VALIDOS = ['Abierto', 'En proceso', 'Cerrado']


class CrearReporte(RolRequeridoMixin, CreateView):
    roles_permitidos = ('residente',)
    model = ReporteDano
    form_class = ReporteDanoForm
    template_name = 'reportes/form_reporte.html'
    success_url = reverse_lazy('mis_reportes')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol == 'residente' and not residente_de(request.user):
            messages.error(request, _('Tu usuario no está vinculado a un residente. Pide al administrador que lo vincule.'))
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        # Se sugiere la ubicación de la unidad del residente
        initial = super().get_initial()
        residente = residente_de(self.request.user)
        unidad = residente.id_unidad_fk if residente else None
        if unidad:
            initial.update({'torre': unidad.torre, 'piso': unidad.piso})
        return initial

    def form_valid(self, form):
        form.instance.id_residente_fk = residente_de(self.request.user)
        form.instance.estado = 'Abierto'
        messages.success(self.request, _('Reporte enviado. La administración lo revisará pronto.'))
        return super().form_valid(form)


class MisReportes(RolRequeridoMixin, ListView):
    roles_permitidos = ('residente',)
    template_name = 'reportes/mis_reportes.html'
    context_object_name = 'reportes'

    def get_queryset(self):
        return ReporteDano.objects.filter(id_residente_fk__usuario=self.request.user).order_by('-fecha_reporte')


class ListaReportesAdmin(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin',)
    template_name = 'reportes/lista_reportes_admin.html'
    context_object_name = 'reportes'
    paginate_by = 15

    def get_queryset(self):
        queryset = ReporteDano.objects.select_related('id_residente_fk').order_by('-fecha_reporte')
        estado = self.request.GET.get('estado', '')
        if estado in ESTADOS_VALIDOS:
            queryset = queryset.filter(estado=estado)
        categoria = self.request.GET.get('categoria', '')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(Q(descripcion__icontains=buscar) | Q(id_residente_fk__nombres__icontains=buscar)
                                       | Q(id_residente_fk__apellidos__icontains=buscar))
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        conteo = dict(ReporteDano.objects.values_list('estado').annotate(n=Count('pk')))
        contexto.update({
            'estado': self.request.GET.get('estado', ''),
            'categoria': self.request.GET.get('categoria', ''),
            'buscar': self.request.GET.get('buscar', ''),
            'categorias': CATEGORIAS,
            'estados': ESTADOS_VALIDOS,
            'num_abiertos': conteo.get('Abierto', 0),
            'num_proceso': conteo.get('En proceso', 0),
            'num_cerrados': conteo.get('Cerrado', 0),
        })
        return contexto


@rol_requerido('admin')
def cambiar_estado(request, pk):
    reporte = get_object_or_404(ReporteDano, pk=pk)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')

        if nuevo_estado not in ESTADOS_VALIDOS:
            messages.error(request, _('Estado no válido.'))
            return redirigir_a_siguiente(request, 'lista_reportes_admin')

        reporte.estado = nuevo_estado
        reporte.fecha_resolucion = timezone.now() if nuevo_estado == 'Cerrado' else None
        reporte.save(update_fields=['estado', 'fecha_resolucion'])
        messages.success(request, _('Reporte #%(numero)s actualizado a "%(estado)s".') % {'numero': reporte.pk, 'estado': _(nuevo_estado)})

    return redirigir_a_siguiente(request, 'lista_reportes_admin')

from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from residentes.models import Residentes
from usuarios.permisos import rol_requerido, RolRequeridoMixin
from .models import ReporteDano
from .forms import ReporteDanoForm


class CrearReporte(RolRequeridoMixin, CreateView):
    roles_permitidos = ('residente',)
    model = ReporteDano
    form_class = ReporteDanoForm
    template_name = 'reportes/form_reporte.html'
    success_url = reverse_lazy('mis_reportes')

    def form_valid(self, form):
        residente = get_object_or_404(Residentes, usuario=self.request.user)
        form.instance.id_residente_fk = residente
        form.instance.estado = 'Abierto'
        messages.success(self.request, 'Reporte creado correctamente.')
        return super().form_valid(form)


class MisReportes(RolRequeridoMixin, ListView):
    roles_permitidos = ('residente',)
    model = ReporteDano
    template_name = 'reportes/mis_reportes.html'
    context_object_name = 'reportes'

    def get_queryset(self):
        return ReporteDano.objects.filter(id_residente_fk__usuario=self.request.user)


class ListaReportesAdmin(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin',)
    model = ReporteDano
    template_name = 'reportes/lista_reportes_admin.html'
    context_object_name = 'reportes'


ESTADOS_VALIDOS = ['Abierto', 'En proceso', 'Cerrado']


@rol_requerido('admin')
def cambiar_estado(request, pk):
    reporte = get_object_or_404(ReporteDano, pk=pk)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')

        if nuevo_estado not in ESTADOS_VALIDOS:
            messages.error(request, 'Estado no válido.')
            return redirect('lista_reportes_admin')

        reporte.estado = nuevo_estado
        if nuevo_estado == 'Cerrado':
            reporte.fecha_resolucion = timezone.now()
        else:
            reporte.fecha_resolucion = None
        reporte.save()
        messages.success(request, f'Reporte actualizado a "{nuevo_estado}".')

    return redirect('lista_reportes_admin')
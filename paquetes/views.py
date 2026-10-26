from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin, redirigir_a_siguiente, residente_de, rol_requerido
from .forms import EMPRESAS_SUGERIDAS, EntregaPaqueteForm, PaqueteForm
from .models import Paquete


def paquetes_del_residente(usuario):
    """Los paquetes de la unidad del residente (los ve toda la familia de esa unidad)."""
    residente = residente_de(usuario)
    if not residente or not residente.id_unidad_fk_id:
        return Paquete.objects.none()
    return Paquete.objects.filter(id_unidad_fk_id=residente.id_unidad_fk_id)


def _filtrar(request, queryset):
    buscar = request.GET.get('buscar', '').strip()
    if buscar:
        queryset = queryset.filter(Q(numero_guia__icontains=buscar.replace(' ', '')) | Q(destinatario__icontains=buscar)
                                   | Q(empresa__icontains=buscar))
    estado = request.GET.get('estado', '')
    if estado in ('En recepción', 'Entregado'):
        queryset = queryset.filter(estado=estado)
    # Primero los que siguen en recepción ('En recepción' va después de 'Entregado' alfabéticamente)
    return queryset.order_by('-estado', '-fecha_recepcion')


class ListaPaquetes(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin', 'seguridad')
    template_name = 'paquetes/lista_paquetes.html'
    context_object_name = 'paquetes'
    paginate_by = 15

    def get_queryset(self):
        queryset = Paquete.objects.select_related('id_unidad_fk', 'recibido_por', 'entregado_por')
        return _filtrar(self.request, queryset)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update({
            'buscar': self.request.GET.get('buscar', ''),
            'estado': self.request.GET.get('estado', ''),
            'total_recepcion': Paquete.objects.filter(estado='En recepción').count(),
            'entregados_hoy': Paquete.objects.filter(fecha_entrega__date=timezone.localdate()).count(),
        })
        return contexto


class MisPaquetes(RolRequeridoMixin, ListView):
    roles_permitidos = ('residente',)
    template_name = 'paquetes/mis_paquetes.html'
    context_object_name = 'paquetes'
    paginate_by = 15

    def get_queryset(self):
        return _filtrar(self.request, paquetes_del_residente(self.request.user)
                        .select_related('id_unidad_fk'))

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        residente = residente_de(self.request.user)
        contexto.update({
            'residente': residente,
            'buscar': self.request.GET.get('buscar', ''),
            'estado': self.request.GET.get('estado', ''),
            'total_recepcion': paquetes_del_residente(self.request.user).filter(estado='En recepción').count(),
        })
        return contexto


class PaqueteFormMixin:
    roles_permitidos = ('admin', 'seguridad')
    form_class = PaqueteForm
    template_name = 'paquetes/form_paquete.html'
    success_url = reverse_lazy('lista_paquetes')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['empresas'] = EMPRESAS_SUGERIDAS
        return contexto


class CrearPaquete(PaqueteFormMixin, RolRequeridoMixin, CreateView):
    model = Paquete

    def form_valid(self, form):
        form.instance.recibido_por = self.request.user
        form.instance.fecha_recepcion = timezone.now()
        form.instance.estado = 'En recepción'
        messages.success(self.request, _('Paquete con guía %(guia)s registrado para %(unidad)s.')
                         % {'guia': form.instance.numero_guia, 'unidad': form.instance.id_unidad_fk})
        return super().form_valid(form)


class EditarPaquete(PaqueteFormMixin, RolRequeridoMixin, UpdateView):
    """Corrige datos mientras el paquete sigue en recepción."""
    pk_url_kwarg = 'id_paquete'

    def get_queryset(self):
        return Paquete.objects.filter(estado='En recepción')

    def form_valid(self, form):
        messages.success(self.request, _('Paquete %(guia)s actualizado.') % {'guia': form.instance.numero_guia})
        return super().form_valid(form)


@rol_requerido('admin', 'seguridad')
def entregar_paquete(request, id_paquete):
    paquete = get_object_or_404(Paquete.objects.select_related('id_unidad_fk', 'recibido_por', 'entregado_por'),
                                pk=id_paquete)
    if not paquete.pendiente:
        if request.method == 'POST':
            messages.info(request, _('El paquete %(guia)s ya había sido entregado.') % {'guia': paquete.numero_guia})
            return redirigir_a_siguiente(request, 'lista_paquetes')
        return render(request, 'paquetes/entregar_paquete.html', {'paquete': paquete, 'form': None})

    if request.method == 'POST':
        form = EntregaPaqueteForm(request.POST, instance=paquete)
        if form.is_valid():
            paquete = form.save(commit=False)
            paquete.estado = 'Entregado'
            paquete.fecha_entrega = timezone.now()
            paquete.entregado_por = request.user
            paquete.save()
            messages.success(request, _('Paquete %(guia)s entregado a %(nombre)s a las %(hora)s.')
                             % {'guia': paquete.numero_guia, 'nombre': paquete.entregado_a,
                                'hora': f'{timezone.localtime(paquete.fecha_entrega):%H:%M}'})
            return redirigir_a_siguiente(request, 'lista_paquetes')
    else:
        form = EntregaPaqueteForm(instance=paquete, initial={'entregado_a': paquete.destinatario})

    return render(request, 'paquetes/entregar_paquete.html', {
        'paquete': paquete, 'form': form, 'next': request.GET.get('next', request.POST.get('next', '')),
    })

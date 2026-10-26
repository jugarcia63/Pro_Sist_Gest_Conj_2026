from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin, redirigir_a_siguiente, rol_requerido
from usuarios.templatetags.ui import pesos
from .forms import ParqueoForm, TarifaForm
from .models import ParqueoVisitante, TarifaParqueadero


def recaudado_hoy():
    return (ParqueoVisitante.objects.filter(fecha_salida__date=timezone.localdate())
            .aggregate(total=Sum('valor_cobrado'))['total'] or 0)


class ListaParqueos(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin', 'seguridad')
    template_name = 'parqueadero/lista_parqueos.html'
    context_object_name = 'parqueos'
    paginate_by = 15

    def get_queryset(self):
        queryset = ParqueoVisitante.objects.select_related('id_unidad_fk', 'visitante', 'registrado_por')
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(Q(placa__icontains=buscar.replace(' ', '').replace('-', ''))
                                       | Q(conductor__icontains=buscar))
        estado = self.request.GET.get('estado', '')
        if estado in ('Dentro', 'Salió'):
            queryset = queryset.filter(estado=estado)
        # Primero los que siguen dentro, luego el historial
        # ('Dentro' va antes que 'Salió' en orden alfabético)
        return queryset.order_by('estado', '-fecha_ingreso')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        contexto.update({
            'buscar': self.request.GET.get('buscar', ''),
            'estado': self.request.GET.get('estado', ''),
            'total_dentro': ParqueoVisitante.objects.filter(estado='Dentro').count(),
            'salidas_hoy': ParqueoVisitante.objects.filter(fecha_salida__date=hoy).count(),
            'recaudado_hoy': recaudado_hoy(),
            'tarifa': TarifaParqueadero.vigente(),
        })
        return contexto


class CrearParqueo(RolRequeridoMixin, CreateView):
    roles_permitidos = ('admin', 'seguridad')
    model = ParqueoVisitante
    form_class = ParqueoForm
    template_name = 'parqueadero/form_parqueo.html'
    success_url = reverse_lazy('lista_parqueos')

    def get_initial(self):
        inicial = super().get_initial()
        visitante = self.request.GET.get('visitante')
        if visitante and visitante.isdigit():
            inicial['visitante'] = visitante
        return inicial

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['tarifa'] = TarifaParqueadero.vigente()
        return contexto

    def form_valid(self, form):
        tarifa = TarifaParqueadero.vigente()
        form.instance.valor_hora = tarifa.valor_hora
        form.instance.horas_gratis = tarifa.horas_gratis
        form.instance.fecha_ingreso = timezone.now()
        form.instance.registrado_por = self.request.user
        form.instance.estado = 'Dentro'
        messages.success(self.request, _('Ingreso del vehículo %(placa)s registrado a las %(hora)s.')
                         % {'placa': form.instance.placa, 'hora': f'{timezone.localtime():%H:%M}'})
        return super().form_valid(form)


class EditarParqueo(RolRequeridoMixin, UpdateView):
    """Solo para corregir datos mientras el vehículo sigue dentro (la hora de ingreso no se cambia)."""
    roles_permitidos = ('admin', 'seguridad')
    form_class = ParqueoForm
    template_name = 'parqueadero/form_parqueo.html'
    success_url = reverse_lazy('lista_parqueos')
    pk_url_kwarg = 'id_parqueo'

    def get_queryset(self):
        return ParqueoVisitante.objects.filter(estado='Dentro')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['tarifa'] = TarifaParqueadero.vigente()
        return contexto

    def form_valid(self, form):
        messages.success(self.request, _('Registro del vehículo %(placa)s actualizado.') % {'placa': form.instance.placa})
        return super().form_valid(form)


@rol_requerido('admin', 'seguridad')
def salida_parqueo(request, id_parqueo):
    """GET: muestra el tiempo y el valor a cobrar. POST: registra la salida con ese cobro."""
    parqueo = get_object_or_404(ParqueoVisitante.objects.select_related('id_unidad_fk', 'visitante'), pk=id_parqueo)

    if request.method == 'POST':
        if not parqueo.dentro:
            messages.info(request, _('El vehículo %(placa)s ya tenía registrada su salida.') % {'placa': parqueo.placa})
        else:
            parqueo.registrar_salida(request.user)
            messages.success(request, _('Salida de %(placa)s registrada: %(horas)s hora(s) cobrada(s), total %(valor)s.')
                             % {'placa': parqueo.placa, 'horas': parqueo.horas_cobradas,
                                'valor': pesos(parqueo.valor_cobrado)})
        return redirigir_a_siguiente(request, 'lista_parqueos')

    return render(request, 'parqueadero/salida_parqueo.html', {
        'parqueo': parqueo,
        'cobro': parqueo.cobro_actual(),
        'next': request.GET.get('next', ''),
    })


@rol_requerido('admin')
def editar_tarifa(request):
    tarifa = TarifaParqueadero.vigente()
    if request.method == 'POST':
        form = TarifaForm(request.POST, instance=tarifa)
        if form.is_valid():
            form.save()
            messages.success(request, _('Tarifa actualizada. Aplica a los vehículos que entren desde ahora.'))
            return redirect('lista_parqueos')
    else:
        form = TarifaForm(instance=tarifa)
    return render(request, 'parqueadero/form_tarifa.html', {'form': form, 'tarifa': tarifa})

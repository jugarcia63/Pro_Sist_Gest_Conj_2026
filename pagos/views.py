from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import CreateView, ListView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from .forms import PagoForm, PasarelaPagoForm
from .models import Pago
from django.utils.translation import gettext as _


def _total(queryset):
    return queryset.aggregate(total=Sum('valor'))['total'] or 0


def _filtrar_por_estado(queryset, estado):
    """'vencido' no se guarda en la base: es un pago pendiente cuya fecha límite ya pasó."""
    hoy = timezone.localdate()
    if estado == 'pendiente':
        return queryset.filter(estado='Pendiente', fecha_vencimiento__gte=hoy)
    if estado == 'vencido':
        return queryset.filter(estado='Pendiente', fecha_vencimiento__lt=hoy)
    if estado == 'pagado':
        return queryset.filter(estado='Pagado')
    return queryset


class ListaPagosResidente(RolRequeridoMixin, ListView):
    roles_permitidos = ('residente',)
    template_name = 'pagos/lista_pagos_residente.html'
    context_object_name = 'pagos'

    def get_queryset(self):
        return (Pago.objects.filter(id_residente_fk__usuario=self.request.user)
                .order_by('-estado', 'fecha_vencimiento'))

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        mios = self.get_queryset()
        pendientes = mios.filter(estado='Pendiente')
        contexto.update({
            'hoy': timezone.localdate(),
            'total_pendiente': _total(pendientes),
            'num_pendientes': pendientes.count(),
            'num_vencidos': pendientes.filter(fecha_vencimiento__lt=timezone.localdate()).count(),
            'total_pagado': _total(mios.filter(estado='Pagado')),
        })
        return contexto


class ListaPagosAdmin(RolRequeridoMixin, ListView):
    """El admin genera y consulta los cobros; no puede marcarlos como pagados."""
    roles_permitidos = ('admin',)
    template_name = 'pagos/lista_pagos_admin.html'
    context_object_name = 'pagos'
    paginate_by = 20

    def get_queryset(self):
        queryset = Pago.objects.select_related('id_residente_fk__id_unidad_fk').order_by('-mes_ano', '-id_pago')
        queryset = _filtrar_por_estado(queryset, self.request.GET.get('estado', ''))
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(
                Q(id_residente_fk__nombres__icontains=buscar) | Q(id_residente_fk__apellidos__icontains=buscar)
                | Q(id_residente_fk__num_documento__icontains=buscar)
            )
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        todos = Pago.objects.all()
        contexto.update({
            'hoy': hoy,
            'estado': self.request.GET.get('estado', ''),
            'buscar': self.request.GET.get('buscar', ''),
            'total_pendiente': _total(_filtrar_por_estado(todos, 'pendiente')),
            'total_vencido': _total(_filtrar_por_estado(todos, 'vencido')),
            'num_vencidos': _filtrar_por_estado(todos, 'vencido').count(),
            'recaudado_mes': _total(todos.filter(estado='Pagado', fecha_pago__year=hoy.year,
                                                 fecha_pago__month=hoy.month)),
        })
        return contexto


class CrearPago(RolRequeridoMixin, CreateView):
    """El admin genera el cobro (factura). Siempre queda en estado Pendiente."""
    roles_permitidos = ('admin',)
    model = Pago
    form_class = PagoForm
    template_name = 'pagos/form_pago.html'
    success_url = reverse_lazy('lista_pagos_admin')

    def get_initial(self):
        initial = super().get_initial()
        residente = self.request.GET.get('residente')
        if residente and residente.isdigit():
            initial['id_residente_fk'] = int(residente)
        return initial

    def form_valid(self, form):
        form.instance.estado = 'Pendiente'
        messages.success(self.request, _('Factura generada para %(residente)s.') % {'residente': form.instance.id_residente_fk})
        return super().form_valid(form)


@rol_requerido('admin')
def anular_pago(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    if request.method == 'POST':
        if pago.estado == 'Pagado':
            messages.error(request, _('No se puede anular un pago que ya fue realizado.'))
        else:
            pago.delete()
            messages.success(request, _('Factura anulada.'))
    return redirect('lista_pagos_admin')


@rol_requerido('residente')
@sensitive_post_parameters('numero_tarjeta', 'cvv')
def pasarela_pago(request, pk):
    """Pantalla de pago simulada. Solo el residente dueño del pago puede acceder."""
    pago = get_object_or_404(Pago, pk=pk, id_residente_fk__usuario=request.user)

    if pago.estado == 'Pagado':
        messages.warning(request, _('Este pago ya fue realizado.'))
        return redirect('lista_pagos_residente')

    if request.method == 'POST':
        form = PasarelaPagoForm(request.POST)
        if form.is_valid():
            # Simulación: no se procesa ni se guarda ningún dato de la tarjeta
            ultimos = form.cleaned_data['numero_tarjeta'][-4:]
            pago.estado = 'Pagado'
            pago.fecha_pago = timezone.localdate()
            pago.metodo_pago = f'Tarjeta •••• {ultimos}'
            pago.comprobante_url = ''  # aquí iría el comprobante si hubiera pasarela real
            pago.save()
            messages.success(request, _('Pago de %(concepto)s realizado con éxito.') % {'concepto': _(pago.tipo_pago)})
            return redirect('lista_pagos_residente')
    else:
        form = PasarelaPagoForm()

    return render(request, 'pagos/pasarela_pago.html', {
        'form': form, 'pago': pago, 'concepto': _(pago.tipo_pago),
        'vencido': pago.fecha_vencimiento < timezone.localdate(),
    })

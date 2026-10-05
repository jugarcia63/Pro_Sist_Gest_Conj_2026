from django.contrib.auth.decorators import login_required
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from usuarios.permisos import RolRequeridoMixin
from .models import Pago
from .forms import PagoForm, PasarelaPagoForm


class ListaPagosResidente(RolRequeridoMixin, ListView):
    roles_permitidos = ('residente',)
    model = Pago
    template_name = 'pagos/lista_pagos_residente.html'
    context_object_name = 'pagos'

    def get_queryset(self):
        return Pago.objects.filter(id_residente_fk__usuario=self.request.user)


class ListaPagosAdmin(RolRequeridoMixin, ListView):
    """Vista de solo lectura para el admin — no puede marcar pagos, solo generarlos y consultarlos."""
    roles_permitidos = ('admin',)
    model = Pago
    template_name = 'pagos/lista_pagos_admin.html'
    context_object_name = 'pagos'


class CrearPago(RolRequeridoMixin, CreateView):
    """El admin genera el cobro (factura). Siempre queda en estado Pendiente."""
    roles_permitidos = ('admin',)
    model = Pago
    form_class = PagoForm
    template_name = 'pagos/form_pago.html'
    success_url = reverse_lazy('lista_pagos_admin')

    def form_valid(self, form):
        form.instance.estado = 'Pendiente'
        messages.success(self.request, 'Factura generada correctamente.')
        return super().form_valid(form)


@login_required
@sensitive_post_parameters('numero_tarjeta', 'cvv')
def pasarela_pago(request, pk):
    """Pantalla de checkout simulada. Solo el residente dueño del pago puede acceder."""
    pago = get_object_or_404(Pago, pk=pk, id_residente_fk__usuario=request.user)

    if pago.estado == 'Pagado':
        messages.warning(request, 'Este pago ya fue realizado.')
        return redirect('lista_pagos_residente')

    if request.method == 'POST':
        form = PasarelaPagoForm(request.POST)
        if form.is_valid():
            # Simulación: no se procesa ni se guarda ningún dato real de tarjeta
            pago.estado = 'Pagado'
            pago.fecha_pago = timezone.now().date()
            pago.metodo_pago = 'Tarjeta (simulado)'
            pago.comprobante_url = ''  # aquí iría el comprobante si hubiera pasarela real
            pago.save()
            messages.success(request, f'Pago de ${pago.valor} realizado con éxito.')
            return redirect('lista_pagos_residente')
    else:
        form = PasarelaPagoForm()

    return render(request, 'pagos/pasarela_pago.html', {'form': form, 'pago': pago})
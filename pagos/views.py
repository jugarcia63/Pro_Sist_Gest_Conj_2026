from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from .models import Pago
from .forms import PagoForm


class ListaPagosResidente(ListView):
    model = Pago
    template_name = 'pagos/lista_pagos_residente.html'
    context_object_name = 'pagos'

    def get_queryset(self):
        return Pago.objects.filter(id_residente_fk__email=self.request.user.email)


class ListaPagosAdmin(ListView):
    model = Pago
    template_name = 'pagos/lista_pagos_admin.html'
    context_object_name = 'pagos'


class CrearPago(CreateView):
    model = Pago
    form_class = PagoForm
    template_name = 'pagos/form_pago.html'
    success_url = reverse_lazy('lista_pagos_admin')


@login_required
def marcar_pagado(request, pk):
    pago = get_object_or_404(Pago, pk=pk)

    if pago.estado == 'Pagado':
        messages.warning(request, 'Este pago ya estaba marcado como pagado.')
        return redirect('lista_pagos_residente')

    pago.estado = 'Pagado'
    pago.fecha_pago = timezone.now().date()
    pago.metodo_pago = pago.metodo_pago or 'Simulado'
    pago.save()
    messages.success(request, f'Pago de {pago.mes_ano.strftime("%B %Y")} marcado como pagado.')
    return redirect('lista_pagos_residente')
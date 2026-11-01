from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin, redirigir_a_siguiente, residente_de, rol_requerido
from .cobros import crear_multa, sincronizar_factura
from .forms import EntregaZonaForm, InventarioFormSet, ReservaForm, ZonaForm
from .models import ItemEntregado, Reservas, ZonasComunes


def _reservas_visibles(usuario):
    """Residente: solo las reservas de su propia unidad. Admin: todas."""
    queryset = Reservas.objects.select_related('id_zona_fk', 'id_unidad_fk')
    if usuario.rol == 'residente':
        residente = residente_de(usuario)
        if not residente or not residente.id_unidad_fk_id:
            return queryset.none()
        return queryset.filter(id_unidad_fk=residente.id_unidad_fk)
    return queryset


# ---------- Zonas comunes ----------

class ListaZonas(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin', 'residente')
    template_name = 'reservas/lista_zonas.html'
    context_object_name = 'zonas'

    def get_queryset(self):
        zonas = ZonasComunes.objects.prefetch_related('inventario').order_by('nombre')
        if self.request.user.rol == 'residente':
            zonas = zonas.filter(estado=1)
        return zonas


class ZonaFormMixin:
    roles_permitidos = ('admin',)
    model = ZonasComunes
    form_class = ZonaForm
    template_name = 'reservas/form_zona.html'
    success_url = reverse_lazy('lista_zonas')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        if 'inventario' not in contexto:
            contexto['inventario'] = InventarioFormSet(instance=self.object or ZonasComunes(), prefix='inventario')
        return contexto

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if 'id_zona' in kwargs else None
        form = self.get_form()
        inventario = InventarioFormSet(request.POST, instance=self.object or ZonasComunes(), prefix='inventario')
        if form.is_valid() and inventario.is_valid():
            with transaction.atomic():
                self.object = form.save()
                inventario.instance = self.object
                inventario.save()
            messages.success(request, _('Zona "%(nombre)s" guardada.') % {'nombre': self.object.nombre})
            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form, inventario=inventario))


class CrearZona(ZonaFormMixin, RolRequeridoMixin, CreateView):
    pass


class EditarZona(ZonaFormMixin, RolRequeridoMixin, UpdateView):
    pk_url_kwarg = 'id_zona'


@rol_requerido('admin')
def eliminar_zona(request, id_zona):
    zona = get_object_or_404(ZonasComunes, pk=id_zona)
    if request.method == 'POST':
        if Reservas.objects.filter(id_zona_fk=zona).exists():
            zona.estado = 0
            zona.save(update_fields=['estado'])
            messages.warning(request, _('"%(zona)s" tiene reservas, así que se marcó como no disponible en vez de borrarse.') % {'zona': zona})
        else:
            zona.delete()
            messages.success(request, _('Zona "%(zona)s" eliminada.') % {'zona': zona})
    return redirect('lista_zonas')


# ---------- Reservas ----------

class ListaReservas(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin', 'residente')
    template_name = 'reservas/lista_reservas.html'
    context_object_name = 'reservas'
    paginate_by = 15

    def get_queryset(self):
        queryset = _reservas_visibles(self.request.user)
        cuando = self.request.GET.get('cuando', 'proximas')
        ahora = timezone.now()
        if cuando == 'pasadas':
            queryset = queryset.filter(fecha_fin__lt=ahora).order_by('-fecha_inicio')
        elif cuando == 'todas':
            queryset = queryset.order_by('-fecha_inicio')
        else:
            queryset = queryset.filter(fecha_fin__gte=ahora).order_by('fecha_inicio')
        estado = self.request.GET.get('estado', '')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        residente = residente_de(usuario) if usuario.rol == 'residente' else None
        contexto.update({
            'cuando': self.request.GET.get('cuando', 'proximas'),
            'estado': self.request.GET.get('estado', ''),
            'ahora': timezone.now(),
            'sin_unidad': usuario.rol == 'residente' and not (residente and residente.id_unidad_fk_id),
            'pendientes': _reservas_visibles(usuario).filter(estado='Pendiente').count(),
        })
        return contexto


class ReservaFormMixin:
    roles_permitidos = ('admin', 'residente')
    model = Reservas
    form_class = ReservaForm
    template_name = 'reservas/form_reserva.html'
    success_url = reverse_lazy('lista_reservas')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol == 'residente':
            residente = residente_de(request.user)
            if not residente or not residente.id_unidad_fk_id:
                messages.error(request, _('Para reservar necesitas tener una unidad asignada. Habla con la administración.'))
                return redirect('lista_reservas')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['es_residente'] = self.request.user.rol == 'residente'
        return kwargs

    def form_valid(self, form):
        if self.request.user.rol == 'residente':
            form.instance.id_unidad_fk = residente_de(self.request.user).id_unidad_fk
            # Cualquier cambio del residente vuelve a quedar pendiente de aprobación
            form.instance.estado = 'Pendiente'
        if not form.instance.pk:
            form.instance.reservado_por = self.request.user
        form.instance.calcular_cobro()
        respuesta = super().form_valid(form)
        aviso = sincronizar_factura(self.object)
        if aviso:
            messages.info(self.request, aviso)
        return respuesta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        zonas = ZonasComunes.objects.filter(estado=1).order_by('nombre')
        contexto['zonas'] = zonas
        # Para el cálculo del valor estimado en el navegador (static/js/app.js)
        contexto['tarifas_zonas'] = {
            str(z.pk): {'hora': float(z.valor_hora), 'limpieza': float(z.valor_limpieza) if z.ofrece_limpieza else None}
            for z in zonas
        }
        return contexto


class CrearReserva(ReservaFormMixin, RolRequeridoMixin, CreateView):

    def get_initial(self):
        initial = super().get_initial()
        zona = self.request.GET.get('zona')
        if zona and zona.isdigit():
            initial['id_zona_fk'] = int(zona)
        return initial

    def form_valid(self, form):
        form.instance.fecha_reserva = timezone.now()
        if self.request.user.rol == 'residente':
            messages.success(self.request, _('Reserva registrada. Queda pendiente de aprobación.'))
        else:
            messages.success(self.request, _('Reserva registrada.'))
        return super().form_valid(form)


class EditarReserva(ReservaFormMixin, RolRequeridoMixin, UpdateView):
    pk_url_kwarg = 'id_reservas'

    def get_queryset(self):
        queryset = _reservas_visibles(self.request.user).filter(fecha_entrega__isnull=True).exclude(estado='Finalizada')
        if self.request.user.rol == 'residente':
            # El residente solo puede cambiar reservas que no se han usado ni cerrado
            queryset = queryset.filter(fecha_inicio__gt=timezone.now(), estado__in=('Pendiente', 'Aprobada'))
        return queryset

    def form_valid(self, form):
        messages.success(self.request, _('Reserva actualizada.'))
        return super().form_valid(form)


@rol_requerido('admin', 'residente')
def cambiar_estado_reserva(request, id_reservas):
    reserva = get_object_or_404(_reservas_visibles(request.user), pk=id_reservas)
    if request.method != 'POST':
        return redirect('lista_reservas')

    nuevo = request.POST.get('estado')
    permitidos = ('Aprobada', 'Rechazada', 'Cancelada', 'Pendiente') if request.user.rol == 'admin' else ('Cancelada',)

    if nuevo not in permitidos:
        messages.error(request, _('No puedes poner la reserva en ese estado.'))
    elif request.user.rol == 'residente' and reserva.fecha_inicio <= timezone.now():
        messages.error(request, _('Solo se pueden cancelar reservas que todavía no han empezado.'))
    elif nuevo == 'Aprobada' and Reservas.objects.filter(
            id_zona_fk=reserva.id_zona_fk, estado='Aprobada',
            fecha_inicio__lt=reserva.fecha_fin, fecha_fin__gt=reserva.fecha_inicio).exclude(pk=reserva.pk).exists():
        messages.error(request, _('Ya hay otra reserva aprobada para esa zona en ese horario.'))
    elif reserva.entregada or reserva.estado == 'Finalizada':
        messages.error(request, _('Esta reserva ya terminó y la zona fue recibida.'))
    else:
        reserva.estado = nuevo
        if reserva.valor_total is None:
            reserva.calcular_cobro()  # reservas hechas antes de que existieran las tarifas
        reserva.save()
        messages.success(request, _('Reserva de %(zona)s marcada como %(estado)s.') % {'zona': reserva.id_zona_fk, 'estado': _(nuevo).lower()})
        aviso = sincronizar_factura(reserva)
        if aviso:
            messages.info(request, aviso)
    return redirigir_a_siguiente(request, 'lista_reservas')


# ---------- Entrega de la zona y comprobante ----------

def _por_recibir():
    """Reservas aprobadas que ya empezaron y cuya zona aún no se ha recibido."""
    return (Reservas.objects.select_related('id_zona_fk', 'id_unidad_fk')
            .filter(estado='Aprobada', fecha_entrega__isnull=True, fecha_inicio__lte=timezone.now()))


class ListaEntregas(RolRequeridoMixin, ListView):
    """Portería y administración: zonas por recibir y las ya recibidas."""
    roles_permitidos = ('admin', 'seguridad')
    template_name = 'reservas/lista_entregas.html'
    context_object_name = 'recibidas'
    paginate_by = 15

    def get_queryset(self):
        return (Reservas.objects.select_related('id_zona_fk', 'id_unidad_fk', 'recibida_por')
                .filter(fecha_entrega__isnull=False).order_by('-fecha_entrega'))

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        ahora = timezone.now()
        contexto.update({
            'por_recibir': _por_recibir().order_by('fecha_fin'),
            'en_uso_pronto': (Reservas.objects.select_related('id_zona_fk', 'id_unidad_fk')
                              .filter(estado='Aprobada', fecha_inicio__gt=ahora,
                                      fecha_inicio__date=timezone.localdate()).order_by('fecha_inicio')),
            'ahora': ahora,
        })
        return contexto


@rol_requerido('admin', 'seguridad')
def recibir_zona(request, id_reservas):
    reserva = get_object_or_404(Reservas.objects.select_related('id_zona_fk', 'id_unidad_fk'), pk=id_reservas)
    if reserva.entregada:
        messages.info(request, _('Esta zona ya fue recibida.'))
        return redirect('lista_entregas')
    if reserva.estado != 'Aprobada' or reserva.fecha_inicio > timezone.now():
        messages.error(request, _('Solo se recibe una zona de una reserva aprobada que ya empezó.'))
        return redirect('lista_entregas')

    items = reserva.id_zona_fk.inventario.all() if reserva.id_zona_fk else []
    if request.method == 'POST':
        form = EntregaZonaForm(request.POST, reserva=reserva, items=items)
        if form.is_valid():
            datos = form.cleaned_data
            with transaction.atomic():
                total = Decimal('0')
                for item in form.items:
                    entregado = ItemEntregado.objects.create(
                        reserva=reserva, item=item, nombre=item.nombre, cantidad_prestada=item.cantidad,
                        faltantes=datos[f'faltan_{item.pk}'] or 0, danados=datos[f'danados_{item.pk}'] or 0,
                        valor_reposicion=item.valor_reposicion,
                    )
                    total += entregado.cargo
                reserva.zona_limpia = datos.get('zona_limpia', True)
                if not reserva.incluye_limpieza and reserva.zona_limpia is False and reserva.id_zona_fk.ofrece_limpieza:
                    total += reserva.id_zona_fk.valor_limpieza  # se cobra la limpieza que no hicieron
                reserva.valor_multa = total
                reserva.observaciones_entrega = datos.get('observaciones_entrega', '')
                reserva.fecha_entrega = timezone.now()
                reserva.recibida_por = request.user
                reserva.estado = 'Finalizada'
                reserva.save()
                multa = crear_multa(reserva)
            if multa:
                from usuarios.templatetags.ui import pesos
                messages.warning(request, _('Zona recibida con novedades: se generó una multa de %(valor)s.')
                                 % {'valor': pesos(multa.valor)})
            else:
                messages.success(request, _('Zona recibida completa. ¡Todo en orden!'))
            return redirect('lista_entregas')
    else:
        form = EntregaZonaForm(reserva=reserva, items=items)
    return render(request, 'reservas/recibir_zona.html', {'reserva': reserva, 'form': form})


@rol_requerido('admin', 'residente', 'seguridad')
def comprobante_reserva(request, id_reservas):
    """PDF con la información de la reserva: lo descarga el residente de la unidad o la administración."""
    from .comprobante import generar_pdf

    if request.user.rol == 'seguridad':
        reservas = Reservas.objects.filter(fecha_entrega__isnull=False)
    else:
        reservas = _reservas_visibles(request.user)
    reserva = get_object_or_404(reservas.select_related('id_zona_fk', 'id_unidad_fk', 'reservado_por', 'recibida_por'),
                                pk=id_reservas)
    respuesta = HttpResponse(generar_pdf(reserva), content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="reserva-{reserva.pk}.pdf"'
    return respuesta

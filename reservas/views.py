from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permisos import RolRequeridoMixin, redirigir_a_siguiente, residente_de, rol_requerido
from .forms import ReservaForm, ZonaForm
from .models import Reservas, ZonasComunes
from django.utils.translation import gettext as _


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
        zonas = ZonasComunes.objects.order_by('nombre')
        if self.request.user.rol == 'residente':
            zonas = zonas.filter(estado=1)
        return zonas


class ZonaFormMixin:
    roles_permitidos = ('admin',)
    model = ZonasComunes
    form_class = ZonaForm
    template_name = 'reservas/form_zona.html'
    success_url = reverse_lazy('lista_zonas')

    def form_valid(self, form):
        messages.success(self.request, _('Zona "%(nombre)s" guardada.') % {'nombre': form.instance.nombre})
        return super().form_valid(form)


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
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['zonas'] = ZonasComunes.objects.filter(estado=1).order_by('nombre')
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
        queryset = _reservas_visibles(self.request.user)
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
    else:
        reserva.estado = nuevo
        reserva.save(update_fields=['estado'])
        messages.success(request, _('Reserva de %(zona)s marcada como %(estado)s.') % {'zona': reserva.id_zona_fk, 'estado': _(nuevo).lower()})
    return redirigir_a_siguiente(request, 'lista_reservas')

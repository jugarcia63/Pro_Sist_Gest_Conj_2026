from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView

from .forms import AsignarPasswordForm, CuentaResidenteForm, GuardiaForm, usuario_sugerido
from .models import Usuario
from .permisos import RolRequeridoMixin, residente_de, rol_requerido


class MiLoginView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True


class CambiarPasswordView(PasswordChangeView):
    """Igual al PasswordChangeView estándar, pero además apaga la bandera
    de 'contraseña pendiente de cambiar' cuando el cambio tiene éxito."""
    template_name = 'usuarios/cambiar_password.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.debe_cambiar_password = False
        self.request.user.save(update_fields=['debe_cambiar_password'])
        return response


def inicio(request):
    return redirect('dashboard' if request.user.is_authenticated else 'login')


# ---------- Personal de seguridad (lo administra el admin) ----------

class ListaGuardias(RolRequeridoMixin, ListView):
    roles_permitidos = ('admin',)
    template_name = 'usuarios/lista_guardias.html'
    context_object_name = 'guardias'

    def get_queryset(self):
        queryset = Usuario.objects.filter(rol='seguridad').order_by('-is_active', 'first_name', 'last_name')
        buscar = self.request.GET.get('buscar', '').strip()
        if buscar:
            queryset = queryset.filter(Q(username__icontains=buscar) | Q(first_name__icontains=buscar)
                                       | Q(last_name__icontains=buscar))
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        todos = Usuario.objects.filter(rol='seguridad')
        contexto.update({
            'buscar': self.request.GET.get('buscar', ''),
            'total_activos': todos.filter(is_active=True).count(),
            'total_inactivos': todos.filter(is_active=False).count(),
        })
        return contexto


class GuardiaFormMixin:
    roles_permitidos = ('admin',)
    model = Usuario
    form_class = GuardiaForm
    template_name = 'usuarios/form_guardia.html'
    success_url = reverse_lazy('lista_guardias')

    def get_queryset(self):
        return Usuario.objects.filter(rol='seguridad')


class CrearGuardia(GuardiaFormMixin, RolRequeridoMixin, CreateView):

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Cuenta de seguridad creada. Usuario para entrar: "%(usuario)s".')
                         % {'usuario': self.object.username})
        return response


class EditarGuardia(GuardiaFormMixin, RolRequeridoMixin, UpdateView):

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['con_password'] = False
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('Datos de %(nombre)s actualizados.') % {'nombre': form.instance.get_full_name()})
        return super().form_valid(form)


@rol_requerido('admin')
def eliminar_guardia(request, pk):
    guardia = get_object_or_404(Usuario, pk=pk, rol='seguridad')
    if request.method == 'POST':
        from paquetes.models import Paquete
        from parqueadero.models import ParqueoVisitante
        from visitantes.models import Visitantes
        nombre = guardia.get_full_name() or guardia.username
        tiene_historial = (
            Visitantes.objects.filter(autorizado_por=guardia).exists()
            or ParqueoVisitante.objects.filter(Q(registrado_por=guardia) | Q(salida_por=guardia)).exists()
            or Paquete.objects.filter(Q(recibido_por=guardia) | Q(entregado_por=guardia)).exists()
        )
        if tiene_historial:
            # Tiene ingresos registrados a su nombre: se conserva el historial y solo se le quita el acceso
            guardia.is_active = False
            guardia.save(update_fields=['is_active'])
            messages.warning(request, _('%(nombre)s tiene registros en portería, así que se desactivó su cuenta '
                                        'en lugar de borrarla.') % {'nombre': nombre})
        else:
            guardia.delete()
            messages.success(request, _('Cuenta de %(nombre)s eliminada.') % {'nombre': nombre})
    return redirect('lista_guardias')


@rol_requerido('admin')
def crear_cuenta_residente(request, id_residente):
    """Solo la administración crea cuentas: aquí le da usuario y contraseña temporal a un residente."""
    from residentes.models import Residentes
    residente = get_object_or_404(Residentes.objects.select_related('id_unidad_fk', 'usuario'), pk=id_residente)
    if residente.usuario_id:
        messages.info(request, _('%(nombre)s ya tiene la cuenta @%(usuario)s. Si la olvidó, asígnale una contraseña nueva.')
                      % {'nombre': residente, 'usuario': residente.usuario.username})
        return redirect('lista_residentes')

    if request.method == 'POST':
        form = CuentaResidenteForm(residente, request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, _('Cuenta @%(usuario)s creada para %(nombre)s. Entrégale la contraseña temporal; '
                                        'al entrar deberá cambiarla.') % {'usuario': usuario.username, 'nombre': residente})
            return redirect('lista_residentes')
    else:
        form = CuentaResidenteForm(residente, initial={'username': usuario_sugerido(residente)})

    return render(request, 'usuarios/crear_cuenta_residente.html', {'form': form, 'residente': residente})


@rol_requerido('admin')
def asignar_password(request, pk):
    """El admin escribe una contraseña nueva para un residente o vigilante que la olvidó."""
    usuario = get_object_or_404(Usuario, pk=pk, rol__in=('residente', 'seguridad'))
    volver = 'lista_guardias' if usuario.rol == 'seguridad' else 'lista_residentes'

    if request.method == 'POST':
        form = AsignarPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Contraseña de "%(usuario)s" actualizada.') % {'usuario': usuario.username})
            return redirect(volver)
    else:
        form = AsignarPasswordForm(usuario)

    return render(request, 'usuarios/asignar_password.html', {'form': form, 'cuenta': usuario, 'volver': volver})


# ---------- Paneles ----------

def _total(queryset):
    return queryset.aggregate(total=Sum('valor'))['total'] or 0


def _contexto_admin():
    from pagos.models import Pago
    from reportes.models import ReporteDano
    from reservas.models import Reservas
    from residentes.models import Residentes, Unidades
    from visitantes.models import Visitantes

    ahora = timezone.now()
    hoy = timezone.localdate()
    pendientes = Pago.objects.filter(estado='Pendiente')
    pagados_mes = Pago.objects.filter(estado='Pagado', fecha_pago__year=hoy.year, fecha_pago__month=hoy.month)

    return {
        'total_residentes': Residentes.objects.count(),
        'total_unidades': Unidades.objects.count(),
        'total_guardias': Usuario.objects.filter(rol='seguridad', is_active=True).count(),
        'pagos_pendientes': pendientes.count(),
        'valor_pendiente': _total(pendientes),
        'recaudado_mes': _total(pagados_mes),
        'reportes_abiertos': ReporteDano.objects.filter(estado='Abierto').count(),
        'reservas_pendientes': Reservas.objects.filter(estado='Pendiente').count(),
        'visitantes_dentro': Visitantes.objects.filter(estado='Dentro').count(),
        'ultimos_reportes': ReporteDano.objects.select_related('id_residente_fk').order_by('-fecha_reporte')[:5],
        'proximas_reservas': Reservas.objects.select_related('id_zona_fk', 'id_unidad_fk')
            .filter(fecha_inicio__gte=ahora).exclude(estado__in=('Cancelada', 'Rechazada'))
            .order_by('fecha_inicio')[:5],
        'pagos_vencidos': pendientes.select_related('id_residente_fk')
            .filter(fecha_vencimiento__lt=hoy).order_by('fecha_vencimiento')[:5],
    }


def _contexto_residente(usuario):
    from pagos.models import Pago
    from reportes.models import ReporteDano
    from reservas.models import Reservas
    from vehiculos.models import Vehiculos

    from paquetes.views import paquetes_del_residente

    residente = residente_de(usuario)
    if not residente:
        return {'residente': None}

    pendientes = Pago.objects.filter(id_residente_fk=residente, estado='Pendiente').order_by('fecha_vencimiento')
    reservas = Reservas.objects.none()
    if residente.id_unidad_fk_id:
        reservas = (Reservas.objects.select_related('id_zona_fk')
                    .filter(id_unidad_fk=residente.id_unidad_fk, fecha_inicio__gte=timezone.now())
                    .exclude(estado__in=('Cancelada', 'Rechazada')).order_by('fecha_inicio'))

    paquetes_en_recepcion = (paquetes_del_residente(usuario).filter(estado='En recepción')
                             .order_by('-fecha_recepcion'))

    return {
        'residente': residente,
        'pagos_pendientes': pendientes.count(),
        'valor_pendiente': _total(pendientes),
        'proximo_pago': pendientes.first(),
        'proximas_reservas': reservas[:4],
        'total_reservas': reservas.count(),
        'reportes_abiertos': ReporteDano.objects.filter(id_residente_fk=residente).exclude(estado='Cerrado').count(),
        'ultimos_reportes': ReporteDano.objects.filter(id_residente_fk=residente).order_by('-fecha_reporte')[:3],
        'total_vehiculos': Vehiculos.objects.filter(id_residente_fk=residente).count(),
        'paquetes_recepcion': paquetes_en_recepcion,
        'total_paquetes': paquetes_en_recepcion.count(),
    }


def _contexto_seguridad():
    from paquetes.models import Paquete
    from parqueadero.models import ParqueoVisitante
    from parqueadero.views import recaudado_hoy
    from vehiculos.models import Vehiculos
    from visitantes.models import Visitantes

    hoy = timezone.localdate()
    dentro = Visitantes.objects.select_related('id_residente_fk__id_unidad_fk').filter(estado='Dentro')
    parqueos = (ParqueoVisitante.objects.select_related('id_unidad_fk', 'visitante')
                .filter(estado='Dentro').order_by('fecha_ingreso'))
    paquetes = Paquete.objects.select_related('id_unidad_fk').filter(estado='En recepción').order_by('-fecha_recepcion')
    return {
        'visitantes_dentro': dentro.order_by('-fecha_ingreso'),
        'total_dentro': dentro.count(),
        'ingresos_hoy': Visitantes.objects.filter(fecha_ingreso__date=hoy).count(),
        'salidas_hoy': Visitantes.objects.filter(fecha_salida__date=hoy).count(),
        'total_vehiculos': Vehiculos.objects.count(),
        'parqueos_dentro': parqueos,
        'total_parqueos': parqueos.count(),
        'recaudado_hoy': recaudado_hoy(),
        'paquetes_recepcion': paquetes[:8],
        'total_paquetes': paquetes.count(),
    }


@login_required
def dashboard(request):
    rol = request.user.rol
    if rol == 'admin':
        template, contexto = 'usuarios/dashboard_admin.html', _contexto_admin()
    elif rol == 'seguridad':
        template, contexto = 'usuarios/dashboard_seguridad.html', _contexto_seguridad()
    else:
        template, contexto = 'usuarios/dashboard_residente.html', _contexto_residente(request.user)
    hora = timezone.localtime().hour
    contexto['saludo'] = _('Buenos días') if hora < 12 else _('Buenas tardes') if hora < 19 else _('Buenas noches')
    contexto['usuario'] = request.user
    contexto['hoy'] = timezone.localdate()
    return render(request, template, contexto)

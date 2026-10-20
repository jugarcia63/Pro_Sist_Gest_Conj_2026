from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, FormView, ListView, UpdateView

from .forms import AsignarPasswordForm, GuardiaForm, RegistroForm
from .models import Usuario
from .permisos import RolRequeridoMixin, residente_de, rol_requerido


class MiLoginView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True


class RegistroView(FormView):
    """El residente crea su cuenta eligiendo su nombre de usuario y su contraseña."""
    template_name = 'usuarios/registro.html'
    form_class = RegistroForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        usuario = form.save()
        login(self.request, usuario, backend='usuarios.backends.UsuarioSinMayusculasBackend')
        messages.success(self.request, _('¡Bienvenido! Tu cuenta "%(usuario)s" quedó lista.') % {'usuario': usuario.username})
        return redirect('dashboard')


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
        from visitantes.models import Visitantes
        nombre = guardia.get_full_name() or guardia.username
        if Visitantes.objects.filter(autorizado_por=guardia).exists():
            # Tiene ingresos registrados a su nombre: se conserva el historial y solo se le quita el acceso
            guardia.is_active = False
            guardia.save(update_fields=['is_active'])
            messages.warning(request, _('%(nombre)s tiene visitas registradas, así que se desactivó su cuenta '
                                        'en lugar de borrarla.') % {'nombre': nombre})
        else:
            guardia.delete()
            messages.success(request, _('Cuenta de %(nombre)s eliminada.') % {'nombre': nombre})
    return redirect('lista_guardias')


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

    residente = residente_de(usuario)
    if not residente:
        return {'residente': None}

    pendientes = Pago.objects.filter(id_residente_fk=residente, estado='Pendiente').order_by('fecha_vencimiento')
    reservas = Reservas.objects.none()
    if residente.id_unidad_fk_id:
        reservas = (Reservas.objects.select_related('id_zona_fk')
                    .filter(id_unidad_fk=residente.id_unidad_fk, fecha_inicio__gte=timezone.now())
                    .exclude(estado__in=('Cancelada', 'Rechazada')).order_by('fecha_inicio'))

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
    }


def _contexto_seguridad():
    from vehiculos.models import Vehiculos
    from visitantes.models import Visitantes

    hoy = timezone.localdate()
    dentro = Visitantes.objects.select_related('id_residente_fk__id_unidad_fk').filter(estado='Dentro')
    return {
        'visitantes_dentro': dentro.order_by('-fecha_ingreso'),
        'total_dentro': dentro.count(),
        'ingresos_hoy': Visitantes.objects.filter(fecha_ingreso__date=hoy).count(),
        'salidas_hoy': Visitantes.objects.filter(fecha_salida__date=hoy).count(),
        'total_vehiculos': Vehiculos.objects.count(),
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

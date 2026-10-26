"""Menú lateral según el rol del usuario, con la sección activa marcada y contadores."""
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from .permisos import residente_de


def _item(texto, ruta, icono, rutas_activas=(), contador=0):
    return {
        'texto': texto,
        'url': reverse(ruta),
        'icono': icono,
        'rutas': (ruta,) + tuple(rutas_activas),
        'contador': contador,
    }


def _menu_admin():
    from pagos.models import Pago
    from reportes.models import ReporteDano
    from reservas.models import Reservas

    hoy = timezone.localdate()
    return [
        (_('General'), [
            _item(_('Inicio'), 'dashboard', 'inicio'),
        ]),
        (_('Comunidad'), [
            _item(_('Residentes'), 'lista_residentes', 'residentes', ('crear_residente', 'editar_residente')),
            _item(_('Unidades'), 'lista_unidades', 'edificio', ('crear_unidad', 'editar_unidad')),
            _item(_('Vehículos'), 'lista_vehiculos', 'carro', ('crear_vehiculo', 'editar_vehiculo')),
            _item(_('Visitantes'), 'lista_visitantes', 'visitante', ('crear_visitante', 'editar_visitante')),
            _item(_('Parqueadero visitantes'), 'lista_parqueos', 'parqueadero',
                  ('crear_parqueo', 'editar_parqueo', 'salida_parqueo', 'editar_tarifa')),
            _item(_('Paquetes'), 'lista_paquetes', 'paquete', ('crear_paquete', 'editar_paquete', 'entregar_paquete')),
            _item(_('Seguridad'), 'lista_guardias', 'escudo', ('crear_guardia', 'editar_guardia')),
        ]),
        (_('Operación'), [
            _item(_('Zonas comunes'), 'lista_zonas', 'zona', ('crear_zona', 'editar_zona')),
            _item(_('Reservas'), 'lista_reservas', 'calendario', ('crear_reserva', 'editar_reserva'),
                  Reservas.objects.filter(estado='Pendiente').count()),
            _item(_('Pagos'), 'lista_pagos_admin', 'tarjeta', ('crear_pago',),
                  Pago.objects.filter(estado='Pendiente', fecha_vencimiento__lt=hoy).count()),
            _item(_('Reportes'), 'lista_reportes_admin', 'alerta', (),
                  ReporteDano.objects.filter(estado='Abierto').count()),
        ]),
    ]


def _menu_residente(usuario):
    from pagos.models import Pago
    from paquetes.views import paquetes_del_residente

    pendientes = Pago.objects.filter(id_residente_fk__usuario=usuario, estado='Pendiente').count()
    paquetes = paquetes_del_residente(usuario).filter(estado='En recepción').count()
    return [
        (_('General'), [
            _item(_('Inicio'), 'dashboard', 'inicio'),
            _item(_('Mis pagos'), 'lista_pagos_residente', 'tarjeta', ('pasarela_pago',), pendientes),
        ]),
        (_('Mi conjunto'), [
            _item(_('Reservas'), 'lista_reservas', 'calendario', ('crear_reserva', 'editar_reserva')),
            _item(_('Zonas comunes'), 'lista_zonas', 'zona'),
            _item(_('Mis vehículos'), 'lista_vehiculos', 'carro', ('crear_vehiculo', 'editar_vehiculo')),
            _item(_('Mis paquetes'), 'mis_paquetes', 'paquete', (), paquetes),
            _item(_('Mis reportes'), 'mis_reportes', 'alerta', ('crear_reporte',)),
        ]),
    ]


def _menu_seguridad():
    from paquetes.models import Paquete
    from parqueadero.models import ParqueoVisitante
    from visitantes.models import Visitantes

    dentro = Visitantes.objects.filter(estado='Dentro').count()
    return [
        (_('General'), [
            _item(_('Inicio'), 'dashboard', 'inicio'),
        ]),
        (_('Portería'), [
            _item(_('Visitantes'), 'lista_visitantes', 'visitante', ('crear_visitante', 'editar_visitante'), dentro),
            _item(_('Parqueadero visitantes'), 'lista_parqueos', 'parqueadero',
                  ('crear_parqueo', 'editar_parqueo', 'salida_parqueo'),
                  ParqueoVisitante.objects.filter(estado='Dentro').count()),
            _item(_('Paquetes'), 'lista_paquetes', 'paquete', ('crear_paquete', 'editar_paquete', 'entregar_paquete'),
                  Paquete.objects.filter(estado='En recepción').count()),
            _item(_('Vehículos'), 'lista_vehiculos', 'carro'),
        ]),
    ]


def navegacion(request):
    usuario = getattr(request, 'user', None)
    if not usuario or not usuario.is_authenticated:
        return {}

    if usuario.rol == 'admin':
        secciones = _menu_admin()
    elif usuario.rol == 'seguridad':
        secciones = _menu_seguridad()
    else:
        secciones = _menu_residente(usuario)

    secciones.append((_('Cuenta'), [_item(_('Cambiar contraseña'), 'cambiar_password', 'llave', ('password_change_done',))]))

    ruta_actual = request.resolver_match.url_name if request.resolver_match else None
    for _titulo, items in secciones:
        for item in items:
            item['activo'] = ruta_actual in item['rutas']

    residente = residente_de(usuario) if usuario.rol == 'residente' else None
    nombre = (f"{residente.nombres or ''} {residente.apellidos or ''}".strip() if residente else '') \
        or usuario.get_full_name() or usuario.username

    return {
        'menu': secciones,
        'nombre_visible': nombre,
        'iniciales': ''.join(p[0] for p in nombre.split()[:2]).upper() or usuario.username[:2].upper(),
    }

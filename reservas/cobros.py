"""Facturas que generan las reservas: el uso de la zona (al aprobarla) y las multas (al recibirla)."""
from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext as _

from pagos.models import Pago
from residentes.models import Residentes

DIAS_PARA_PAGAR_MULTA = 15


def residente_que_paga(reserva):
    """Quien hizo la reserva; si la hizo el admin, el primer residente de la unidad."""
    usuario = reserva.reservado_por
    residente = getattr(usuario, 'residente', None) if usuario else None
    if residente is None and reserva.id_unidad_fk_id:
        residente = Residentes.objects.filter(id_unidad_fk_id=reserva.id_unidad_fk_id).order_by('pk').first()
    return residente


def sincronizar_factura(reserva):
    """Mantiene la factura del uso de la zona al día con la reserva.

    - Aprobada y con valor: crea la factura, o actualiza la pendiente si cambió el valor o la fecha.
    - Pendiente, rechazada o cancelada: anula la factura pendiente (una ya pagada no se toca).
    Devuelve un texto para mostrar al usuario, o None si no hubo nada que avisar."""
    facturas = Pago.objects.filter(id_reserva_fk=reserva, tipo_pago='Reserva')
    pendiente = facturas.filter(estado='Pendiente').first()

    if reserva.estado != 'Aprobada' or not reserva.valor_total:
        if pendiente:
            pendiente.delete()
            return _('Se anuló la factura pendiente de esta reserva.')
        return None

    if facturas.filter(estado='Pagado').exists():
        return None

    residente = residente_que_paga(reserva)
    if residente is None:
        return _('No se generó la factura: la unidad no tiene residentes registrados.')

    fecha_uso = timezone.localtime(reserva.fecha_inicio)
    datos = {
        'id_residente_fk': residente,
        'valor': reserva.valor_total,
        'mes_ano': fecha_uso.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        # Se paga antes de usar la zona (o el mismo día si se aprueba tarde)
        'fecha_vencimiento': max(fecha_uso.date(), timezone.localdate()),
    }
    if pendiente:
        for campo, valor in datos.items():
            setattr(pendiente, campo, valor)
        pendiente.save()
        return None
    Pago.objects.create(id_reserva_fk=reserva, tipo_pago='Reserva', estado='Pendiente', **datos)
    return _('Se generó la factura de %(valor)s por el uso de la zona.') % {'valor': _pesos(reserva.valor_total)}


def crear_multa(reserva):
    """Factura por implementos faltantes o dañados y por entregar sucia la zona sin servicio de limpieza."""
    if not reserva.valor_multa:
        return None
    residente = residente_que_paga(reserva)
    if residente is None:
        return None
    hoy = timezone.localdate()
    return Pago.objects.create(
        id_residente_fk=residente, id_reserva_fk=reserva, tipo_pago='Multa', estado='Pendiente',
        valor=reserva.valor_multa, mes_ano=timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        fecha_vencimiento=hoy + timedelta(days=DIAS_PARA_PAGAR_MULTA),
    )


def _pesos(valor):
    from usuarios.templatetags.ui import pesos
    return pesos(valor)

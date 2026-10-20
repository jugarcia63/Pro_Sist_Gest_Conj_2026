from decimal import Decimal, InvalidOperation

from django import template
from django.utils.html import format_html

register = template.Library()

# Estado (tal como se guarda en la base) -> clase de color del badge
COLORES_ESTADO = {
    'pagado': 'exito', 'aprobada': 'exito', 'cerrado': 'exito', 'activo': 'exito', 'salió': 'neutro',
    'pendiente': 'aviso', 'en proceso': 'aviso', 'dentro': 'info',
    'vencido': 'error', 'abierto': 'error', 'rechazada': 'error', 'cancelada': 'neutro', 'inactivo': 'neutro',
}


@register.simple_tag
def icono(nombre, clase=''):
    return format_html('<svg class="ico {}" aria-hidden="true"><use href="#i-{}"></use></svg>', clase, nombre)


@register.filter
def pesos(valor):
    """320000.00 -> $320.000"""
    try:
        numero = Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        return valor
    return '$' + f'{numero:,.0f}'.replace(',', '.')


@register.filter
def color_estado(estado):
    return COLORES_ESTADO.get(str(estado or '').strip().lower(), 'neutro')


@register.filter
def traducir(valor, por_defecto=''):
    """Traduce un valor guardado en la base (p. ej. 'Pendiente'). Si está vacío, usa el texto por defecto.
    A diferencia de {% translate variable %}, no falla cuando el valor es None."""
    from django.utils.translation import gettext
    texto = valor if valor not in (None, '') else por_defecto
    return gettext(str(texto)) if texto else ''

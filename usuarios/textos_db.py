"""Valores que se guardan tal cual en la base de datos (en español) y que las plantillas
muestran traducidos con {% translate valor %}. Este archivo solo existe para que el
script de traducciones los incluya en el catálogo; no se importa en ningún lado."""
from django.utils.translation import gettext_noop as N_

VALORES_GUARDADOS = [
    # Estados de reservas, pagos, reportes, visitantes y vehículos
    N_('Pendiente'), N_('Aprobada'), N_('Rechazada'), N_('Cancelada'),
    N_('Pagado'), N_('Vencido'),
    N_('Abierto'), N_('En proceso'), N_('Cerrado'),
    N_('Dentro'), N_('Salió'),
    N_('Activo'), N_('Inactivo'),
    # Estados de paquetes
    N_('En recepción'), N_('Entregado'),
    # Tipos de vehículo
    N_('Carro'), N_('Moto'),
    # Categorías de reportes
    N_('Plomería'), N_('Eléctrico'), N_('Estructural'), N_('Ascensor'), N_('Zonas comunes'), N_('Seguridad'), N_('Otro'),
    # Conceptos de pago
    N_('Administración'), N_('Reserva'), N_('Multa'), N_('Parqueadero'),
    # Roles
    N_('Residente'), N_('Administrador'),
    # Textos por defecto en plantillas
    N_('Sin estado'), N_('Sin categoría'),
]

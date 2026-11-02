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
    # Reserva cuya zona ya fue recibida
    N_('Finalizada'),
    # Reserva pendiente que nadie aprobó antes de su horario
    N_('Vencida'),
    # Movimientos del inventario
    N_('Pérdida'), N_('Daño'), N_('Reparado'), N_('Dado de baja'), N_('Compra o reposición'),
    # Tipos de vehículo
    N_('Carro'), N_('Moto'),
    # Categorías de reportes
    N_('Plomería'), N_('Eléctrico'), N_('Estructural'), N_('Ascensor'), N_('Zonas comunes'), N_('Seguridad'), N_('Otro'),
    # Conceptos de pago
    N_('Administración'), N_('Reserva'), N_('Multa'), N_('Parqueadero'),
    # Meses (reporte de recaudo)
    N_('Enero'), N_('Febrero'), N_('Marzo'), N_('Abril'), N_('Mayo'), N_('Junio'), N_('Julio'), N_('Agosto'),
    N_('Septiembre'), N_('Octubre'), N_('Noviembre'), N_('Diciembre'),
    # Columnas del reporte de recaudo
    N_('Reservas'), N_('Multas'), N_('Parq. residentes'), N_('Parq. visitantes'), N_('Otros'),
    # Roles
    N_('Residente'), N_('Administrador'),
    # Textos por defecto en plantillas
    N_('Sin estado'), N_('Sin categoría'),
]

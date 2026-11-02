"""Pone al día los datos de ejemplo: borra lo que depende de la fecha y lo vuelve a crear con fechas de hoy.

    python manage.py refrescar_datos --si

Borra: visitas, parqueos de visitantes, paquetes, reservas (con sus entregas), pagos, reportes de daños,
avisos y movimientos del inventario. El inventario vuelve a sus cantidades de la lista base.
No toca: usuarios, residentes, unidades, zonas comunes, vehículos ni la tarifa del parqueadero.

Sirve para que la demo no muestre facturas de hace meses como vencidas, reportes viejos abiertos
o reservas pendientes que ya pasaron. En Render se ejecuta solo si la variable REFRESCAR_DATOS=1
(ver build.sh); después de un deploy conviene quitarla para no borrar lo que se cargue a mano.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from usuarios import datos_recientes
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Borra los datos que dependen de la fecha (pagos, reservas, visitas...) y los crea de nuevo con fechas de hoy.'

    def add_arguments(self, parser):
        parser.add_argument('--si', action='store_true',
                            help='Confirma que se pueden borrar los pagos, reservas, visitas y demás datos con fecha.')

    def handle(self, *args, **options):
        if not options['si']:
            raise CommandError('Esto borra pagos, reservas, visitas, paquetes, reportes y avisos. '
                               'Si estás seguro, ejecuta: python manage.py refrescar_datos --si')
        if not Usuario.objects.filter(username='laura.gomez').exists():
            raise CommandError('No están los datos de ejemplo base. Ejecuta primero: python manage.py poblar_datos')

        with transaction.atomic():
            datos_recientes.borrar()
            resumen = datos_recientes.generar()

        self.stdout.write(self.style.SUCCESS('Datos de ejemplo actualizados a la fecha de hoy:'))
        for nombre, cantidad in resumen.items():
            self.stdout.write(f'  {nombre}: {cantidad}')

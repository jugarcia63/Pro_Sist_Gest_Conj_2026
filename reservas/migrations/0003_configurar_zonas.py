from django.db import migrations
from django.utils import timezone


def configurar(apps, schema_editor):
    """Precios, limpieza e inventario inicial para las zonas que ya existen (p. ej. en Render).
    Solo toca zonas sin configurar; ver reservas/datos_iniciales.py."""
    from reservas.datos_iniciales import configurar_zonas
    configurar_zonas(apps.get_model('reservas', 'ZonasComunes'), apps.get_model('reservas', 'ItemInventario'))


def reservas_viejas_sin_cobro(apps, schema_editor):
    """Las reservas que ya empezaron se hicieron cuando todo era gratis: quedan con valor 0.
    Las futuras quedan sin valor y se calculan con la tarifa nueva cuando se aprueben."""
    Reservas = apps.get_model('reservas', 'Reservas')
    ahora = timezone.now()
    (Reservas.objects.filter(valor_total__isnull=True, fecha_inicio__lt=ahora)
     .update(valor_hora=0, valor_limpieza=0, horas_cobradas=0, valor_total=0))
    # Las aprobadas que ya terminaron se usaron antes de existir la entrega con inventario:
    # se cierran para que no aparezcan como "por recibir" en portería.
    Reservas.objects.filter(estado='Aprobada', fecha_fin__lt=ahora, fecha_entrega__isnull=True).update(estado='Finalizada')


class Migration(migrations.Migration):

    dependencies = [
        ('reservas', '0002_cobro_inventario_entrega'),
    ]

    operations = [
        migrations.RunPython(configurar, migrations.RunPython.noop),
        migrations.RunPython(reservas_viejas_sin_cobro, migrations.RunPython.noop),
    ]

from decimal import Decimal

from django.db import migrations


def crear_tarifa(apps, schema_editor):
    """Tarifa de arranque: $2.000 por hora, las primeras 2 horas gratis. El admin la cambia desde la página."""
    TarifaParqueadero = apps.get_model('parqueadero', 'TarifaParqueadero')
    if not TarifaParqueadero.objects.exists():
        TarifaParqueadero.objects.create(valor_hora=Decimal('2000'), horas_gratis=2)


class Migration(migrations.Migration):

    dependencies = [
        ('parqueadero', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_tarifa, migrations.RunPython.noop),
    ]

"""Configuración inicial de las zonas comunes: precios, servicio de limpieza e inventario.

Se aplica una sola vez por zona (la usa la migración 0002 y el comando poblar_datos). Una zona
que ya tiene inventario o un precio configurado no se toca, así nunca se pisa lo que el admin cambió.

Criterio del inventario: lo que el conjunto PRESTA con la zona y se puede perder o dañar
(no lo fijo, como la piscina o los columpios). El valor de reposición es lo que se cobra
como multa si el implemento falta o se devuelve dañado.
"""
from decimal import Decimal

# nombre de la zona: (valor por hora, ofrece limpieza, valor limpieza, [(implemento, cantidad, valor reposición)])
ZONAS = {
    'Salón social': (25000, True, 40000, [
        ('Mesas plegables', 10, 180000),
        ('Sillas', 60, 45000),
        ('Manteles', 10, 35000),
        ('Equipo de sonido con 2 parlantes', 1, 900000),
        ('Micrófono inalámbrico', 1, 150000),
        ('Cafetera grande', 1, 250000),
    ]),
    'Zona BBQ': (15000, True, 30000, [
        ('Parrilla a gas', 1, 1500000),
        ('Pinzas para asar', 2, 25000),
        ('Espátulas', 2, 20000),
        ('Cepillo para parrilla', 1, 30000),
        ('Bandejas', 4, 20000),
        ('Mesas', 4, 180000),
        ('Sillas', 16, 45000),
    ]),
    'Piscina': (0, False, 0, [
        ('Sillas asoleadoras', 8, 250000),
        ('Sombrillas', 4, 180000),
        ('Flotadores', 6, 30000),
    ]),
    'Gimnasio': (0, False, 0, [
        ('Colchonetas', 8, 60000),
        ('Mancuernas (par)', 10, 80000),
        ('Balones de pilates', 4, 70000),
    ]),
    'Cancha múltiple': (0, False, 0, [
        ('Balón de microfútbol', 2, 90000),
        ('Balón de baloncesto', 2, 110000),
        ('Petos', 12, 15000),
    ]),
    'Salón de juegos': (0, False, 0, [
        ('Tacos de billar', 4, 70000),
        ('Juego de bolas de billar', 1, 250000),
        ('Raquetas de ping-pong', 4, 40000),
        ('Pelotas de ping-pong', 6, 3000),
        ('Juegos de mesa', 6, 80000),
    ]),
}


def configurar_zonas(Zona, Item):
    """Recibe las clases de modelo (en una migración vienen de apps.get_model)."""
    for zona in Zona.objects.filter(nombre__in=ZONAS):
        valor_hora, limpieza, valor_limpieza, implementos = ZONAS[zona.nombre]
        sin_configurar = (not zona.valor_hora and not zona.ofrece_limpieza
                          and not Item.objects.filter(zona=zona).exists())
        if not sin_configurar:
            continue
        zona.valor_hora = Decimal(valor_hora)
        zona.ofrece_limpieza = limpieza
        zona.valor_limpieza = Decimal(valor_limpieza)
        zona.save(update_fields=['valor_hora', 'ofrece_limpieza', 'valor_limpieza'])
        Item.objects.bulk_create([
            Item(zona=zona, nombre=nombre, cantidad=cantidad, valor_reposicion=Decimal(valor))
            for nombre, cantidad, valor in implementos
        ])

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
        ('Video beam con telón', 1, 1800000),
        ('Extensión eléctrica de 10 m', 2, 45000),
        ('Vajilla (puesto completo)', 60, 18000),
    ]),
    'Zona BBQ': (15000, True, 30000, [
        ('Parrilla a gas', 1, 1500000),
        ('Pinzas para asar', 2, 25000),
        ('Espátulas', 2, 20000),
        ('Cepillo para parrilla', 1, 30000),
        ('Bandejas', 4, 20000),
        ('Mesas', 4, 180000),
        ('Sillas', 16, 45000),
        ('Pipeta de gas 40 lb', 1, 220000),
        ('Extintor', 1, 120000),
    ]),
    'Piscina': (0, False, 0, [
        ('Sillas asoleadoras', 8, 250000),
        ('Sombrillas', 4, 180000),
        ('Flotadores', 6, 30000),
        ('Tablas de natación', 6, 35000),
        ('Aro salvavidas', 2, 150000),
    ]),
    'Gimnasio': (0, False, 0, [
        ('Colchonetas', 8, 60000),
        ('Mancuernas (par)', 10, 80000),
        ('Balones de pilates', 4, 70000),
        ('Bandas elásticas', 6, 25000),
        ('Kettlebells', 4, 120000),
        ('Lazos de saltar', 6, 15000),
    ]),
    'Cancha múltiple': (0, False, 0, [
        ('Balón de microfútbol', 2, 90000),
        ('Balón de baloncesto', 2, 110000),
        ('Petos', 12, 15000),
        ('Balón de voleibol', 1, 80000),
        ('Red de voleibol', 1, 150000),
        ('Conos de entrenamiento', 10, 6000),
    ]),
    'Parque infantil': (0, False, 0, [
        ('Kit de arenero (balde y pala)', 6, 15000),
        ('Balones infantiles', 3, 25000),
    ]),
    'Salón de juegos': (0, False, 0, [
        ('Tacos de billar', 4, 70000),
        ('Juego de bolas de billar', 1, 250000),
        ('Raquetas de ping-pong', 4, 40000),
        ('Pelotas de ping-pong', 6, 3000),
        ('Juegos de mesa', 6, 80000),
        ('Ajedrez', 2, 60000),
        ('Dominó', 2, 30000),
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


def _clave(texto):
    """Compara nombres sin tildes, mayúsculas ni espacios de más ('Salón Social ' == 'salon social')."""
    import unicodedata
    texto = unicodedata.normalize('NFKD', (texto or '').strip().lower())
    return ' '.join(''.join(c for c in texto if not unicodedata.combining(c)).split())


def completar_inventario(Zona, Item):
    """Agrega a cada zona los implementos de la lista que todavía no tiene (por nombre).
    No cambia cantidades ni precios de lo que ya existe y no borra nada. Devuelve cuántos agregó."""
    por_clave = {_clave(nombre): datos for nombre, datos in ZONAS.items()}
    agregados = 0
    for zona in Zona.objects.all():
        datos = por_clave.get(_clave(zona.nombre))
        if not datos:
            continue
        existentes = {_clave(n) for n in Item.objects.filter(zona=zona).values_list('nombre', flat=True)}
        nuevos = [Item(zona=zona, nombre=nombre, cantidad=cantidad, valor_reposicion=Decimal(valor))
                  for nombre, cantidad, valor in datos[3] if _clave(nombre) not in existentes]
        Item.objects.bulk_create(nuevos)
        agregados += len(nuevos)
    return agregados

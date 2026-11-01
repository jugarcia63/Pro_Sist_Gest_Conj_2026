import math
from decimal import Decimal

from django.conf import settings
from django.db import models

from residentes.models import Unidades


def horas_a_cobrar(inicio, fin):
    """Cada hora iniciada se cobra completa, desde el primer segundo (sin horas gratis).
    Ej.: 2 h exactas = 2 horas; 2 h y 1 segundo = 3 horas."""
    if not inicio or not fin or fin <= inicio:
        return 0
    return math.ceil((fin - inicio).total_seconds() / 3600)


class ZonasComunes(models.Model):
    id_zona = models.AutoField(db_column='Id_Zona', primary_key=True)
    nombre = models.CharField(db_column='Nombre', max_length=100, blank=True, null=True)
    descripcion = models.CharField(db_column='Descripcion', max_length=250, blank=True, null=True)
    capacidad = models.IntegerField(db_column='Capacidad', blank=True, null=True)
    reglas = models.TextField(db_column='Reglas', blank=True, null=True)
    estado = models.IntegerField(db_column='Estado', blank=True, null=True)
    # Cobro: 0 = zona gratuita. La limpieza es opcional y solo si la zona la ofrece.
    valor_hora = models.DecimalField(db_column='Valor_Hora', max_digits=10, decimal_places=2, default=Decimal('0'))
    ofrece_limpieza = models.BooleanField(db_column='Ofrece_Limpieza', default=False)
    valor_limpieza = models.DecimalField(db_column='Valor_Limpieza', max_digits=10, decimal_places=2,
                                         default=Decimal('0'))

    class Meta:
        managed = True
        db_table = 'zonas_comunes'

    def __str__(self):
        return self.nombre or ''

    @property
    def es_paga(self):
        return bool(self.valor_hora and self.valor_hora > 0)


class ItemInventario(models.Model):
    """Implemento que el conjunto presta con la zona (parrilla, sillas, balones...)."""
    id_item = models.AutoField(db_column='Id_Item', primary_key=True)
    zona = models.ForeignKey(ZonasComunes, models.CASCADE, db_column='Id_Zona_FK', related_name='inventario')
    nombre = models.CharField(db_column='Nombre', max_length=100)
    cantidad = models.PositiveIntegerField(db_column='Cantidad', default=1)
    valor_reposicion = models.DecimalField(db_column='Valor_Reposicion', max_digits=10, decimal_places=2,
                                           default=Decimal('0'))

    class Meta:
        db_table = 'inventario_zonas'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.cantidad} × {self.nombre}'


class Reservas(models.Model):
    id_reservas = models.AutoField(db_column='Id_Reservas', primary_key=True)
    id_zona_fk = models.ForeignKey(ZonasComunes, models.DO_NOTHING, db_column='Id_Zona_FK', blank=True, null=True)
    id_unidad_fk = models.ForeignKey(Unidades, models.DO_NOTHING, db_column='Id_Unidad_FK', blank=True, null=True)
    fecha_reserva = models.DateTimeField(db_column='Fecha_Reserva', blank=True, null=True)
    fecha_inicio = models.DateTimeField(db_column='Fecha_Inicio', blank=True, null=True)
    fecha_fin = models.DateTimeField(db_column='Fecha_Fin', blank=True, null=True)
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)
    observaciones = models.TextField(db_column='Observaciones', blank=True, null=True)
    reservado_por = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, db_column='Reservado_Por',
                                      blank=True, null=True, related_name='reservas_hechas')

    # Cobro: la tarifa se copia al reservar, así un cambio de precio no afecta reservas ya hechas
    incluye_limpieza = models.BooleanField(db_column='Incluye_Limpieza', default=False)
    valor_hora = models.DecimalField(db_column='Valor_Hora', max_digits=10, decimal_places=2,
                                     blank=True, null=True)
    valor_limpieza = models.DecimalField(db_column='Valor_Limpieza', max_digits=10, decimal_places=2,
                                         blank=True, null=True)
    horas_cobradas = models.PositiveIntegerField(db_column='Horas_Cobradas', blank=True, null=True)
    valor_total = models.DecimalField(db_column='Valor_Total', max_digits=12, decimal_places=2,
                                      blank=True, null=True)

    # Entrega de la zona (la revisa seguridad o la administración)
    fecha_entrega = models.DateTimeField(db_column='Fecha_Entrega', blank=True, null=True)
    recibida_por = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, db_column='Recibida_Por',
                                     blank=True, null=True, related_name='zonas_recibidas')
    zona_limpia = models.BooleanField(db_column='Zona_Limpia', blank=True, null=True)
    observaciones_entrega = models.TextField(db_column='Observaciones_Entrega', blank=True, default='')
    valor_multa = models.DecimalField(db_column='Valor_Multa', max_digits=12, decimal_places=2,
                                      blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'reservas'

    def __str__(self):
        return f"{self.id_zona_fk} - {self.fecha_inicio}"

    @property
    def entregada(self):
        return self.fecha_entrega is not None

    @property
    def valor_horas(self):
        return (self.valor_hora or 0) * (self.horas_cobradas or 0)

    def calcular_cobro(self):
        """Copia la tarifa vigente de la zona y calcula horas y total (horas reservadas)."""
        zona = self.id_zona_fk
        self.valor_hora = zona.valor_hora if zona else Decimal('0')
        if not (zona and zona.ofrece_limpieza):
            self.incluye_limpieza = False
        self.valor_limpieza = zona.valor_limpieza if self.incluye_limpieza else Decimal('0')
        self.horas_cobradas = horas_a_cobrar(self.fecha_inicio, self.fecha_fin)
        self.valor_total = self.valor_hora * self.horas_cobradas + self.valor_limpieza


class ItemEntregado(models.Model):
    """Resultado de revisar un implemento cuando se recibe la zona. Copia nombre y valor del inventario."""
    id_item_entregado = models.AutoField(db_column='Id_Item_Entregado', primary_key=True)
    reserva = models.ForeignKey(Reservas, models.CASCADE, db_column='Id_Reserva_FK', related_name='items_entregados')
    item = models.ForeignKey(ItemInventario, models.SET_NULL, db_column='Id_Item_FK', blank=True, null=True)
    nombre = models.CharField(db_column='Nombre', max_length=100)
    cantidad_prestada = models.PositiveIntegerField(db_column='Cantidad_Prestada')
    faltantes = models.PositiveIntegerField(db_column='Faltantes', default=0)
    danados = models.PositiveIntegerField(db_column='Danados', default=0)
    valor_reposicion = models.DecimalField(db_column='Valor_Reposicion', max_digits=10, decimal_places=2,
                                           default=Decimal('0'))

    class Meta:
        db_table = 'items_entregados'
        ordering = ['nombre']

    @property
    def en_buen_estado(self):
        return self.cantidad_prestada - self.faltantes - self.danados

    @property
    def cargo(self):
        return (self.faltantes + self.danados) * self.valor_reposicion

    @property
    def completo(self):
        return self.faltantes == 0 and self.danados == 0

import math
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from residentes.models import Unidades
from visitantes.models import Visitantes


class TarifaParqueadero(models.Model):
    """Tarifa vigente del parqueadero de visitantes. Siempre hay una sola fila (la crea la migración)."""
    valor_hora = models.DecimalField(db_column='Valor_Hora', max_digits=10, decimal_places=2, default=Decimal('2000'))
    horas_gratis = models.PositiveSmallIntegerField(db_column='Horas_Gratis', default=2)
    actualizado = models.DateTimeField(db_column='Actualizado', auto_now=True)

    class Meta:
        db_table = 'tarifa_parqueadero'

    def __str__(self):
        return f'{self.valor_hora} / hora ({self.horas_gratis} h gratis)'

    @classmethod
    def vigente(cls):
        tarifa = cls.objects.order_by('pk').first()
        return tarifa or cls.objects.create()


def calcular_cobro(ingreso, salida, valor_hora, horas_gratis):
    """Devuelve (minutos, horas_cobradas, valor).

    Se cuentan minutos completos; cada hora iniciada cuenta como hora entera y se descuentan
    las horas gratis. Ej.: 2 h gratis y 2 h 10 min dentro = 3 horas iniciadas - 2 = 1 hora cobrada."""
    minutos = max(0, int((salida - ingreso).total_seconds() // 60))
    horas_iniciadas = math.ceil(minutos / 60)
    horas_cobradas = max(0, horas_iniciadas - (horas_gratis or 0))
    return minutos, horas_cobradas, Decimal(valor_hora or 0) * horas_cobradas


class ParqueoVisitante(models.Model):
    TIPOS = [('Carro', 'Carro'), ('Moto', 'Moto')]
    ESTADOS = [('Dentro', 'Dentro'), ('Salió', 'Salió')]

    id_parqueo = models.AutoField(db_column='Id_Parqueo', primary_key=True)
    placa = models.CharField(db_column='Placa', max_length=10)
    tipo_vehiculo = models.CharField(db_column='Tipo_Vehiculo', max_length=20, choices=TIPOS, default='Carro')
    id_unidad_fk = models.ForeignKey(Unidades, models.PROTECT, db_column='Id_Unidad_FK', related_name='parqueos')
    visitante = models.ForeignKey(Visitantes, models.SET_NULL, db_column='Id_Visitante_FK', blank=True, null=True,
                                  related_name='parqueos')
    conductor = models.CharField(db_column='Conductor', max_length=150, blank=True, default='')
    observaciones = models.CharField(db_column='Observaciones', max_length=255, blank=True, default='')
    fecha_ingreso = models.DateTimeField(db_column='Fecha_Ingreso', default=timezone.now)
    fecha_salida = models.DateTimeField(db_column='Fecha_Salida', blank=True, null=True)
    # La tarifa se copia al entrar: si el admin la cambia, no afecta a los carros que ya están dentro
    valor_hora = models.DecimalField(db_column='Valor_Hora', max_digits=10, decimal_places=2)
    horas_gratis = models.PositiveSmallIntegerField(db_column='Horas_Gratis')
    horas_cobradas = models.PositiveIntegerField(db_column='Horas_Cobradas', blank=True, null=True)
    valor_cobrado = models.DecimalField(db_column='Valor_Cobrado', max_digits=12, decimal_places=2, blank=True, null=True)
    estado = models.CharField(db_column='Estado', max_length=20, choices=ESTADOS, default='Dentro')
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, db_column='Registrado_Por',
                                       blank=True, null=True, related_name='parqueos_registrados')
    salida_por = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, db_column='Salida_Por',
                                   blank=True, null=True, related_name='parqueos_cerrados')

    class Meta:
        db_table = 'parqueo_visitantes'
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return self.placa

    @property
    def dentro(self):
        return self.estado == 'Dentro'

    def cobro(self, hasta=None):
        """(minutos, horas_cobradas, valor) hasta la salida registrada, o hasta ahora si sigue dentro."""
        fin = self.fecha_salida or hasta or timezone.now()
        return calcular_cobro(self.fecha_ingreso, fin, self.valor_hora, self.horas_gratis)

    def cobro_actual(self):
        minutos, horas, valor = self.cobro()
        return {'minutos': minutos, 'horas': horas, 'valor': valor,
                'tiempo': f'{minutos // 60} h {minutos % 60:02d} min'}

    def registrar_salida(self, usuario):
        self.fecha_salida = timezone.now()
        _, self.horas_cobradas, self.valor_cobrado = self.cobro()
        self.estado = 'Salió'
        self.salida_por = usuario
        self.save(update_fields=['fecha_salida', 'horas_cobradas', 'valor_cobrado', 'estado', 'salida_por'])

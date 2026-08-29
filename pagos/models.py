from django.db import models
from residentes.models import Residentes
from reservas.models import Reservas

class Pago(models.Model):
    id_pago = models.AutoField(db_column='Id_Pago', primary_key=True)
    id_residente_fk = models.ForeignKey(Residentes, models.DO_NOTHING, db_column='Id_Residente_FK', blank=True, null=True)
    tipo_pago = models.CharField(db_column='Tipo_Pago', max_length=20)
    id_reserva_fk = models.ForeignKey(Reservas, models.DO_NOTHING, db_column='Id_Reserva_FK', blank=True, null=True)
    mes_ano = models.DateTimeField(db_column='Mes_Año')
    valor = models.DecimalField(db_column='Valor', max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField(db_column='Fecha_Vencimiento')
    fecha_pago = models.DateField(db_column='Fecha_Pago', blank=True, null=True)
    metodo_pago = models.CharField(db_column='Metodo_Pago', max_length=30, blank=True, null=True)
    comprobante_url = models.CharField(db_column='Comprobante_Url', max_length=255, blank=True, null=True)
    estado = models.CharField(db_column='Estado', max_length=20, default='Pendiente')

    class Meta:
        managed = True
        db_table = 'pagos'

    def __str__(self):
        return f"{self.id_residente_fk} - {self.mes_ano} - {self.estado}"
from django.conf import settings
from django.db import models
from django.utils import timezone

from residentes.models import Unidades


class Paquete(models.Model):
    ESTADOS = [('En recepción', 'En recepción'), ('Entregado', 'Entregado')]

    id_paquete = models.AutoField(db_column='Id_Paquete', primary_key=True)
    numero_guia = models.CharField(db_column='Numero_Guia', max_length=60)
    empresa = models.CharField(db_column='Empresa', max_length=80, blank=True, default='')
    destinatario = models.CharField(db_column='Destinatario', max_length=150)
    id_unidad_fk = models.ForeignKey(Unidades, models.PROTECT, db_column='Id_Unidad_FK', related_name='paquetes')
    descripcion = models.CharField(db_column='Descripcion', max_length=255, blank=True, default='')
    fecha_recepcion = models.DateTimeField(db_column='Fecha_Recepcion', default=timezone.now)
    recibido_por = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, db_column='Recibido_Por',
                                     blank=True, null=True, related_name='paquetes_recibidos')
    estado = models.CharField(db_column='Estado', max_length=20, choices=ESTADOS, default='En recepción')
    fecha_entrega = models.DateTimeField(db_column='Fecha_Entrega', blank=True, null=True)
    entregado_a = models.CharField(db_column='Entregado_A', max_length=150, blank=True, default='')
    documento_entrega = models.CharField(db_column='Documento_Entrega', max_length=50, blank=True, default='')
    entregado_por = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, db_column='Entregado_Por',
                                      blank=True, null=True, related_name='paquetes_entregados')

    class Meta:
        db_table = 'paquetes'
        ordering = ['-fecha_recepcion']

    def __str__(self):
        return self.numero_guia

    @property
    def pendiente(self):
        return self.estado == 'En recepción'

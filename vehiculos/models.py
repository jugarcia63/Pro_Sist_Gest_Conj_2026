from django.db import models
from residentes.models import Residentes


class Vehiculos(models.Model):
    id_vehiculo = models.AutoField(db_column='Id_Vehiculo', primary_key=True)
    placa = models.CharField(db_column='Placa', max_length=10, blank=True, null=True)
    marca = models.CharField(db_column='Marca', max_length=50, blank=True, null=True)
    modelo = models.CharField(db_column='Modelo', max_length=50, blank=True, null=True)
    color = models.CharField(db_column='Color', max_length=30, blank=True, null=True)
    id_residente_fk = models.ForeignKey(Residentes, models.DO_NOTHING, db_column='Id_Residente_FK', blank=True, null=True)
    tipo_vehiculo = models.CharField(db_column='Tipo_Vehiculo', max_length=20, blank=True, null=True)
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'vehiculos'

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"
from django.db import models
from residentes.models import Residentes

class ReporteDano(models.Model):
    id_reportes = models.AutoField(db_column='Id_Reportes', primary_key=True)
    id_residente_fk = models.ForeignKey(Residentes, models.DO_NOTHING, db_column='Id_Residente_FK')
    categoria = models.CharField(db_column='Categoria', max_length=50, blank=True, null=True)
    descripcion = models.TextField(db_column='Descripcion')
    torre = models.CharField(db_column='Torre', max_length=10, blank=True, null=True)
    piso = models.IntegerField(db_column='Piso', blank=True, null=True)
    fecha_reporte = models.DateTimeField(db_column='Fecha_Reporte', auto_now_add=True)
    estado = models.CharField(db_column='Estado', max_length=20, default='Abierto')
    asignado_a_fk = models.IntegerField(db_column='Asignado_a_FK', blank=True, null=True)
    fecha_resolucion = models.DateTimeField(db_column='Fecha_Resolucion', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'reportes'

    def __str__(self):
        return f"{self.id_residente_fk} - Torre {self.torre} Piso {self.piso} - {self.estado}"

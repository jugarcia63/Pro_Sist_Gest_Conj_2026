from django.db import models
from residentes.models import Residentes
from usuarios.models import Usuario


class Visitantes(models.Model):
    id_visitante = models.AutoField(db_column='Id_Visitante', primary_key=True)
    nombre = models.CharField(db_column='Nombre', max_length=100, blank=True, null=True)
    apellidos = models.CharField(db_column='Apellidos', max_length=100, blank=True, null=True)
    tipo_documento = models.CharField(db_column='Tipo_Documento', max_length=20, blank=True, null=True)
    num_documento = models.CharField(db_column='Num_Documento', max_length=50, blank=True, null=True)
    telefono = models.CharField(db_column='Telefono', max_length=20, blank=True, null=True)
    motivo = models.CharField(db_column='Motivo', max_length=255, blank=True, null=True)
    id_residente_fk = models.ForeignKey(Residentes, models.DO_NOTHING, db_column='Id_Residente_FK', blank=True, null=True)
    fecha_ingreso = models.DateTimeField(db_column='Fecha_Ingreso', blank=True, null=True)
    fecha_salida = models.DateTimeField(db_column='Fecha_Salida', blank=True, null=True)
    autorizado_por = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='Autorizado_Por', blank=True, null=True)
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'visitantes'

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

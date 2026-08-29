from django.db import models


class Unidades(models.Model):
    id_unidad = models.AutoField(db_column='Id_Unidad', primary_key=True)
    torre = models.CharField(db_column='Torre', max_length=10, blank=True, null=True)
    apto = models.CharField(db_column='Apto', max_length=10, blank=True, null=True)
    piso = models.IntegerField(db_column='Piso', blank=True, null=True)
    area = models.DecimalField(db_column='Area', max_digits=8, decimal_places=2, blank=True, null=True)
    id_residente_fk = models.IntegerField(db_column='Id_Residente_FK', blank=True, null=True)
    estado = models.IntegerField(db_column='Estado', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'unidades'

    def __str__(self):
        return f"Torre {self.torre} - Apto {self.apto}"


class Residentes(models.Model):
    id_residente = models.AutoField(db_column='Id_Residente', primary_key=True)
    tipo_documento = models.CharField(db_column='Tipo_Documento', max_length=100, blank=True, null=True)
    num_documento = models.CharField(db_column='Num_Documento', max_length=100, blank=True, null=True)
    nombres = models.CharField(db_column='Nombres', max_length=255, blank=True, null=True)
    apellidos = models.CharField(db_column='Apellidos', max_length=255, blank=True, null=True)
    telefono = models.CharField(db_column='Telefono', max_length=255, blank=True, null=True)
    email = models.CharField(db_column='Email', max_length=255, blank=True, null=True)
    id_unidad_fk = models.ForeignKey(Unidades, models.DO_NOTHING, db_column='Id_Unidad_FK', blank=True, null=True)
    fecha_registro = models.DateTimeField(db_column='Fecha_Registro', blank=True, null=True)
    estado = models.IntegerField(db_column='Estado', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'residentes'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
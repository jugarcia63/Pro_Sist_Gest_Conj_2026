from django.db import models
from residentes.models import Unidades


class ZonasComunes(models.Model):
    id_zona = models.AutoField(db_column='Id_Zona', primary_key=True)
    nombre = models.CharField(db_column='Nombre', max_length=100, blank=True, null=True)
    descripcion = models.CharField(db_column='Descripcion', max_length=250, blank=True, null=True)
    capacidad = models.IntegerField(db_column='Capacidad', blank=True, null=True)
    reglas = models.TextField(db_column='Reglas', blank=True, null=True)
    estado = models.IntegerField(db_column='Estado', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'zonas_comunes'

    def __str__(self):
        return self.nombre


class Reservas(models.Model):
    id_reservas = models.AutoField(db_column='Id_Reservas', primary_key=True)
    id_zona_fk = models.ForeignKey(ZonasComunes, models.DO_NOTHING, db_column='Id_Zona_FK', blank=True, null=True)
    id_unidad_fk = models.ForeignKey(Unidades, models.DO_NOTHING, db_column='Id_Unidad_FK', blank=True, null=True)
    fecha_reserva = models.DateTimeField(db_column='Fecha_Reserva', blank=True, null=True)
    fecha_inicio = models.DateTimeField(db_column='Fecha_Inicio', blank=True, null=True)
    fecha_fin = models.DateTimeField(db_column='Fecha_Fin', blank=True, null=True)
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)
    observaciones = models.TextField(db_column='Observaciones', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'reservas'

    def __str__(self):
        return f"{self.id_zona_fk} - {self.fecha_inicio}"

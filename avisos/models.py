from django.conf import settings
from django.db import models


class Aviso(models.Model):
    """Notificación dentro de la app para un usuario (paquete que llegó, reserva aprobada, multa...)."""
    TIPOS = [
        ('paquete', 'Paquete'),
        ('reserva', 'Reserva'),
        ('multa', 'Multa'),
        ('factura', 'Factura'),
        ('cuenta', 'Cuenta'),
    ]

    id_aviso = models.AutoField(db_column='Id_Aviso', primary_key=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_column='Id_Usuario_FK',
                                related_name='avisos')
    tipo = models.CharField(db_column='Tipo', max_length=20, choices=TIPOS)
    titulo = models.CharField(db_column='Titulo', max_length=150)
    mensaje = models.CharField(db_column='Mensaje', max_length=300, blank=True, default='')
    url = models.CharField(db_column='Url', max_length=200, blank=True, default='')
    leido = models.BooleanField(db_column='Leido', default=False)
    creado = models.DateTimeField(db_column='Creado', auto_now_add=True)

    class Meta:
        db_table = 'avisos'
        ordering = ['-creado', '-id_aviso']

    def __str__(self):
        return f'{self.usuario} · {self.titulo}'

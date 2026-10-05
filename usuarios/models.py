from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('residente', 'Residente'),
        ('admin', 'Administrador'),
        ('seguridad', 'Seguridad'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='residente')
    debe_cambiar_password = models.BooleanField(
        default=False,
        help_text='Se activa al crear la cuenta o resetear la contraseña; obliga a cambiarla en el próximo login.',
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuarios_usuario_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuarios_usuario_permissions_set',
        blank=True,
    )

    def __str__(self):
        return f"{self.username} ({self.rol})"

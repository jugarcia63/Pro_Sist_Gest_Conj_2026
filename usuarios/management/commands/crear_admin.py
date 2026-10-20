from decouple import config
from django.core.management.base import BaseCommand

from usuarios.models import Usuario


class Command(BaseCommand):
    """Crea la cuenta de administrador a partir de ADMIN_USERNAME y ADMIN_PASSWORD.
    Se ejecuta en cada deploy (build.sh); si el usuario ya existe no cambia su contraseña."""
    help = 'Crea el usuario administrador definido en las variables de entorno.'

    def handle(self, *args, **options):
        username = config('ADMIN_USERNAME', default='')
        password = config('ADMIN_PASSWORD', default='')

        if not username or not password:
            self.stdout.write('ADMIN_USERNAME o ADMIN_PASSWORD sin definir; no se crea administrador.')
            return

        usuario, creado = Usuario.objects.get_or_create(
            username=username,
            defaults={'email': config('ADMIN_EMAIL', default='')},
        )
        if creado:
            usuario.set_password(password)

        usuario.rol = 'admin'
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.is_active = True
        usuario.debe_cambiar_password = False
        usuario.save()

        estado = 'creado' if creado else 'ya existía (contraseña sin cambios)'
        self.stdout.write(self.style.SUCCESS(f'Administrador "{username}" {estado}.'))

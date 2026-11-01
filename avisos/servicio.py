"""Crear avisos y, si los correos están activos, enviar la misma información por email.

Uso:
    from avisos.servicio import avisar, usuarios_de_unidad
    avisar(usuarios_de_unidad(unidad), 'paquete', 'Llegó un paquete para ti', 'Guía 7000…', url=reverse('mis_paquetes'))
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from .models import Aviso

log = logging.getLogger(__name__)


def usuarios_de_unidad(unidad):
    """Cuentas activas de los residentes que viven en esa unidad."""
    from usuarios.models import Usuario
    if unidad is None:
        return Usuario.objects.none()
    return Usuario.objects.filter(residente__id_unidad_fk=unidad, is_active=True)


def url_absoluta(ruta):
    """https://<dominio público>/ruta, para los enlaces de los correos."""
    base = getattr(settings, 'SITIO_URL', '').rstrip('/')
    return f'{base}{ruta}' if base and ruta.startswith('/') else ruta


def correos_activos():
    return getattr(settings, 'CORREOS_ACTIVOS', False)


def enviar_correo(destinatarios, asunto, texto):
    """Envía después de guardar en la base y nunca rompe la página si el envío falla."""
    destinatarios = [c for c in destinatarios if c]
    if not destinatarios or not correos_activos():
        return

    def _enviar():
        for correo in destinatarios:  # uno por persona: nadie ve el correo de los demás
            try:
                send_mail(asunto, texto, None, [correo], fail_silently=False)
            except Exception:  # noqa: BLE001 - un correo fallido no debe tumbar la acción
                log.exception('No se pudo enviar el correo "%s" a %s', asunto, correo)

    transaction.on_commit(_enviar)


def avisar(usuarios, tipo, titulo, mensaje='', url='', correo=True):
    usuarios = [u for u in usuarios if u is not None and u.is_active]
    Aviso.objects.bulk_create([
        Aviso(usuario=u, tipo=tipo, titulo=titulo[:150], mensaje=mensaje[:300], url=url) for u in usuarios
    ])
    if correo:
        cuerpo = mensaje + (f'\n\nVer en la plataforma: {url_absoluta(url)}' if url else '')
        cuerpo += '\n\n— Conjunto Reserva de Madrid'
        enviar_correo([u.email for u in usuarios], f'{titulo} · Conjunto Reserva de Madrid', cuerpo)

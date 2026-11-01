"""Backend de correo que usa la API HTTPS de Brevo en vez de SMTP.

Render (plan gratis) bloquea los puertos SMTP 25, 465 y 587 desde septiembre de 2025, así que
el envío normal por SMTP (por ejemplo, Gmail) no funciona ahí. Una API por HTTPS sí funciona.

Configuración (variables de entorno):
    BREVO_API_KEY     clave de API de Brevo (Settings > SMTP & API > API Keys)
    CORREO_REMITENTE  correo verificado en Brevo como remitente (Senders)
"""
import json
import logging
import urllib.request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

log = logging.getLogger(__name__)

URL_API = 'https://api.brevo.com/v3/smtp/email'


class BrevoEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        enviados = 0
        for mensaje in email_messages:
            datos = {
                'sender': {'email': settings.CORREO_REMITENTE, 'name': settings.CORREO_NOMBRE},
                'to': [{'email': d} for d in mensaje.to],
                'subject': mensaje.subject,
                'textContent': mensaje.body,
            }
            peticion = urllib.request.Request(
                URL_API, data=json.dumps(datos).encode(), method='POST',
                headers={'api-key': settings.BREVO_API_KEY, 'content-type': 'application/json',
                         'accept': 'application/json'},
            )
            try:
                with urllib.request.urlopen(peticion, timeout=8) as respuesta:
                    if 200 <= respuesta.status < 300:
                        enviados += 1
            except Exception:  # noqa: BLE001
                if not self.fail_silently:
                    raise
                log.exception('Brevo no aceptó el correo "%s"', mensaje.subject)
        return enviados

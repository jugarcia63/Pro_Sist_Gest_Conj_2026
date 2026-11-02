"""Cierres automáticos para que las reservas no se queden "pegadas" en un estado viejo.

- Pendiente cuyo horario ya empezó sin que nadie la aprobara -> Vencida (ya no se puede usar).
- Aprobada que terminó hace más de DIAS_PARA_CERRAR días sin que portería recibiera la zona -> Finalizada,
  con una nota. Sin revisión no hay multa: si hubo daños, el administrador los registra en el inventario.

Lo ejecuta el middleware TareasAutomaticasMiddleware (como mucho cada 5 minutos) y el comando
refrescar_datos. Se puede llamar cuantas veces se quiera: solo toca lo que ya venció.
"""
from datetime import timedelta

from django.utils import timezone

DIAS_PARA_CERRAR = 3
NOTA_CIERRE = 'Cerrada automáticamente: portería no registró la entrega de la zona.'


def cerrar_reservas_vencidas(ahora=None):
    from .models import Reservas

    ahora = ahora or timezone.now()
    vencidas = Reservas.objects.filter(estado='Pendiente', fecha_inicio__lte=ahora).update(estado='Vencida')
    cerradas = (Reservas.objects
                .filter(estado='Aprobada', fecha_entrega__isnull=True, fecha_fin__lt=ahora - timedelta(days=DIAS_PARA_CERRAR))
                .update(estado='Finalizada', observaciones_entrega=NOTA_CIERRE))
    return vencidas, cerradas

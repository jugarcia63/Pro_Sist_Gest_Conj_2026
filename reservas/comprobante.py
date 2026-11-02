"""Comprobante en PDF de una reserva (reportlab).

Incluye: datos de la reserva, el cobro (horas × tarifa + limpieza), las facturas asociadas,
el inventario que el conjunto presta con la zona y, si ya se recibió, cómo se devolvió.
"""
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pagos.models import Pago
from usuarios.templatetags.ui import pesos

MORADO = colors.HexColor('#4C1D95')
MORADO_SUAVE = colors.HexColor('#EDE9FE')
VERDE = colors.HexColor('#047857')
ROJO = colors.HexColor('#B91C1C')
GRIS = colors.HexColor('#6B6584')
BORDE = colors.HexColor('#DDD8EC')

ESTILOS = getSampleStyleSheet()
TITULO = ParagraphStyle('titulo', parent=ESTILOS['Title'], fontName='Helvetica-Bold', fontSize=17,
                        textColor=MORADO, alignment=0, spaceAfter=2)
SUBTITULO = ParagraphStyle('sub', parent=ESTILOS['Normal'], fontSize=9.5, textColor=GRIS)
SECCION = ParagraphStyle('seccion', parent=ESTILOS['Heading2'], fontName='Helvetica-Bold', fontSize=12,
                         textColor=MORADO, spaceBefore=10, spaceAfter=5)
TEXTO = ParagraphStyle('texto', parent=ESTILOS['Normal'], fontSize=9.5, leading=13)
CELDA = ParagraphStyle('celda', parent=TEXTO, fontSize=9)
CELDA_DER = ParagraphStyle('celda_der', parent=CELDA, alignment=TA_RIGHT)
NOTA = ParagraphStyle('nota', parent=TEXTO, fontSize=8, textColor=GRIS, leading=11)


def e(valor):
    """Escapa texto escrito por usuarios (reportlab interpreta < y & como marcado)."""
    return escape(str(valor)) if valor not in (None, '') else '—'


def _fecha(valor, formato='%d/%m/%Y %I:%M %p'):
    return timezone.localtime(valor).strftime(formato) if valor else '—'


def _tabla(filas, anchos, encabezado=True, alinear_derecha=()):
    datos = [[Paragraph(str(c), CELDA_DER if i in alinear_derecha else CELDA) for i, c in enumerate(f)] for f in filas]
    tabla = Table(datos, colWidths=anchos, repeatRows=1 if encabezado else 0)
    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, BORDE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    if encabezado:
        estilo += [('BACKGROUND', (0, 0), (-1, 0), MORADO_SUAVE)]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _datos(etiquetas_valores):
    """Tabla de dos columnas etiqueta / valor, sin encabezado."""
    filas = [[f'<b>{e}</b>', v] for e, v in etiquetas_valores]
    tabla = _tabla(filas, [5 * cm, 12 * cm], encabezado=False)
    tabla.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F7F5FC'))]))
    return tabla


def _pie(canvas, doc):
    canvas.saveState()
    ancho, _alto = letter
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.2 * cm, _('Conjunto Reserva de Madrid · Comprobante generado el %(fecha)s')
                      % {'fecha': _fecha(timezone.now())})
    canvas.drawRightString(ancho - 2 * cm, 1.2 * cm, _('Página %(n)s') % {'n': doc.page})
    canvas.restoreState()


def _logo_y_pie(canvas, doc):
    """Primera página: logo del conjunto (tres torres sobre una colina) arriba a la derecha + pie."""
    canvas.saveState()
    ancho, alto = letter
    cx, cy, r = ancho - 2.9 * cm, alto - 2.3 * cm, 0.95 * cm
    canvas.setFillColor(colors.HexColor('#6D28D9'))
    canvas.circle(cx, cy, r, stroke=0, fill=1)
    borde = canvas.beginPath()
    borde.circle(cx, cy, r)
    canvas.clipPath(borde, stroke=0, fill=0)
    canvas.setFillColor(colors.HexColor('#FDE68A'))
    canvas.circle(cx + 0.5 * cm, cy + 0.45 * cm, 0.14 * cm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    for dx, h, w in ((-0.55, 0.7, 0.3), (-0.18, 0.95, 0.36), (0.25, 0.6, 0.3)):
        canvas.rect(cx + dx * cm, cy - 0.3 * cm, w * cm, h * cm, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor('#10B981'))
    canvas.rect(cx - r, cy - r, 2 * r, r - 0.3 * cm, stroke=0, fill=1)
    canvas.restoreState()
    _pie(canvas, doc)


def generar_pdf(reserva):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=2 * cm,
                            title=_('Reserva %(n)s') % {'n': reserva.pk}, author='Conjunto Reserva de Madrid')
    zona = reserva.id_zona_fk
    h = []

    h.append(Paragraph(_('Comprobante de reserva No. %(n)s') % {'n': reserva.pk}, TITULO))
    h.append(Paragraph(_('Conjunto Reserva de Madrid · Madrid, Cundinamarca'), SUBTITULO))

    # Datos generales
    h.append(Paragraph(_('Datos de la reserva'), SECCION))
    reservado_por = reserva.reservado_por
    h.append(_datos([
        (_('Zona común'), e(zona)),
        (_('Unidad'), e(reserva.id_unidad_fk)),
        (_('Reservada por'), e(reservado_por.get_full_name() or reservado_por.username) if reservado_por else '—'),
        (_('Fecha de la solicitud'), _fecha(reserva.fecha_reserva)),
        (_('Horario'), f"{_fecha(reserva.fecha_inicio, '%d/%m/%Y %I:%M %p')} – {_fecha(reserva.fecha_fin, '%I:%M %p')}"),
        (_('Estado'), _(reserva.estado or 'Sin estado')),
        (_('Servicio de limpieza'), _('Incluido') if reserva.incluye_limpieza else _('No; la zona se entrega limpia')),
        (_('Observaciones'), e(reserva.observaciones)),
    ]))

    # Cobro
    h.append(Paragraph(_('Valor de la reserva'), SECCION))
    if reserva.valor_total:
        filas = [[_('Concepto'), _('Detalle'), _('Valor')]]
        if reserva.valor_hora:
            filas.append([_('Uso de la zona'), _('%(h)s hora(s) × %(v)s (cada hora iniciada se cobra completa)')
                          % {'h': reserva.horas_cobradas, 'v': pesos(reserva.valor_hora)}, pesos(reserva.valor_horas)])
        if reserva.incluye_limpieza:
            filas.append([_('Servicio de limpieza'), _('Valor fijo de la zona'), pesos(reserva.valor_limpieza)])
        filas.append([f"<b>{_('Total')}</b>", '', f'<b>{pesos(reserva.valor_total)}</b>'])
        h.append(_tabla(filas, [4.5 * cm, 9.5 * cm, 3 * cm], alinear_derecha=(2,)))
    else:
        h.append(Paragraph(_('Esta zona no tiene costo de uso.'), TEXTO))

    facturas = Pago.objects.filter(id_reserva_fk=reserva).order_by('pk')
    if facturas:
        h.append(Spacer(1, 6))
        filas = [[_('Factura'), _('Concepto'), _('Vence'), _('Estado'), _('Valor')]]
        for f in facturas:
            filas.append([f'#{f.pk}', _(f.tipo_pago), f.fecha_vencimiento.strftime('%d/%m/%Y'), _(f.estado), pesos(f.valor)])
        h.append(_tabla(filas, [2 * cm, 4.5 * cm, 3 * cm, 3.5 * cm, 4 * cm], alinear_derecha=(4,)))

    # Inventario
    if reserva.entregada:
        h.append(Paragraph(_('Entrega de la zona'), SECCION))
        recibio = reserva.recibida_por
        limpieza = (_('A cargo del conjunto (servicio incluido)') if reserva.incluye_limpieza
                    else _('Sí') if reserva.zona_limpia else _('No'))
        h.append(_datos([
            (_('Recibida el'), _fecha(reserva.fecha_entrega)),
            (_('Recibida por'), e(recibio.get_full_name() or recibio.username) if recibio else '—'),
            (_('Zona limpia'), limpieza),
            (_('Observaciones'), e(reserva.observaciones_entrega)),
        ]))
        items = sorted(reserva.items_entregados.all(), key=lambda i: (i.completo, i.nombre))
        if items:
            h.append(Spacer(1, 8))
            filas = [[_('Implemento'), _('Prestados'), _('Bien'), _('Faltan'), _('Dañados'), _('Cargo')]]
            for i in items:
                color = '#B91C1C' if not i.completo else '#047857'
                filas.append([e(i.nombre), i.cantidad_prestada, i.en_buen_estado,
                              f'<font color="{color}">{i.faltantes}</font>', f'<font color="{color}">{i.danados}</font>',
                              pesos(i.cargo) if i.cargo else '—'])
            h.append(_tabla(filas, [6 * cm, 2 * cm, 1.8 * cm, 1.8 * cm, 2 * cm, 3.4 * cm], alinear_derecha=(5,)))
        if reserva.valor_multa:
            h.append(Spacer(1, 6))
            h.append(Paragraph(f'<font color="#B91C1C"><b>{_("Multa por la entrega")}: {pesos(reserva.valor_multa)}</b></font>', TEXTO))
        else:
            h.append(Spacer(1, 6))
            h.append(Paragraph(f'<font color="#047857"><b>{_("Zona entregada completa y en buen estado.")}</b></font>', TEXTO))
    else:
        h.append(Paragraph(_('Implementos que presta el conjunto'), SECCION))
        items = [i for i in zona.inventario.all() if i.disponibles] if zona else []
        if items:
            filas = [[_('Implemento'), _('Cantidad'), _('Valor de reposición')]]
            filas += [[e(i.nombre), i.disponibles, pesos(i.valor_reposicion)] for i in items]
            h.append(_tabla(filas, [9 * cm, 3 * cm, 5 * cm], alinear_derecha=(2,)))
            h.append(Spacer(1, 4))
            h.append(Paragraph(_('Al terminar, portería revisa que se devuelva todo. Lo que falte o llegue dañado '
                                 'se cobra por su valor de reposición.'), NOTA))
        else:
            h.append(Paragraph(_('Esta zona no tiene implementos prestados.'), TEXTO))

    if zona and zona.reglas:
        reglas = [Paragraph(_('Reglas de la zona'), SECCION)]
        reglas += [Paragraph(f'• {e(linea.strip())}', TEXTO) for linea in zona.reglas.splitlines() if linea.strip()]
        h.append(KeepTogether(reglas))

    doc.build(h, onFirstPage=_logo_y_pie, onLaterPages=_pie)
    return buffer.getvalue()

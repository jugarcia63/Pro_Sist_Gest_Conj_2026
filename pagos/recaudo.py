"""Reporte de recaudo por mes y concepto, y sus descargas (Excel/CSV y PDF).

Qué cuenta como recaudado:
- Facturas pagadas (Pago con estado 'Pagado'), en el mes de su fecha de pago, por concepto:
  administración, reservas de zonas, multas, parqueadero de residentes y otros.
- El parqueadero de visitantes que se cobra en portería al registrar la salida (ParqueoVisitante),
  en el mes de esa salida.
"""
import csv
from decimal import Decimal
from io import BytesIO, StringIO

from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from django.utils.translation import gettext as _

from parqueadero.models import ParqueoVisitante
from usuarios.templatetags.ui import pesos
from .models import Pago

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre',
         'Noviembre', 'Diciembre']

# (clave, título de la columna, tipo_pago en la base o None para el parqueadero de visitantes)
CONCEPTOS = [
    ('administracion', 'Administración', 'Administración'),
    ('reservas', 'Reservas', 'Reserva'),
    ('multas', 'Multas', 'Multa'),
    ('parqueadero', 'Parq. residentes', 'Parqueadero'),
    ('visitantes', 'Parq. visitantes', None),
    ('otros', 'Otros', 'Otro'),
]


def anios_disponibles():
    actual = timezone.localdate().year
    primeros = [d.year for d in (Pago.objects.filter(fecha_pago__isnull=False).order_by('fecha_pago')
                                 .values_list('fecha_pago', flat=True)[:1])]
    desde = min(primeros + [actual])
    return list(range(actual, desde - 1, -1))


def calcular(anio):
    """Devuelve {'filas': [12 meses], 'totales': {...}, 'total': Decimal, 'pendiente': {...}}."""
    tabla = {m: {c: Decimal('0') for c, _t, _p in CONCEPTOS} for m in range(1, 13)}

    pagados = (Pago.objects.filter(estado='Pagado', fecha_pago__year=anio)
               .annotate(mes=ExtractMonth('fecha_pago')).values('mes', 'tipo_pago').annotate(total=Sum('valor')))
    por_tipo = {p: c for c, _t, p in CONCEPTOS if p}
    for fila in pagados:
        tabla[fila['mes']][por_tipo.get(fila['tipo_pago'], 'otros')] += fila['total'] or 0

    visitantes = (ParqueoVisitante.objects.filter(fecha_salida__year=anio, valor_cobrado__gt=0)
                  .annotate(mes=ExtractMonth('fecha_salida')).values('mes').annotate(total=Sum('valor_cobrado')))
    for fila in visitantes:
        tabla[fila['mes']]['visitantes'] += fila['total'] or 0

    filas = []
    for mes in range(1, 13):
        valores = tabla[mes]
        filas.append({'mes': mes, 'nombre': _(MESES[mes - 1]), 'valores': [valores[c] for c, _t, _p in CONCEPTOS],
                      'total': sum(valores.values())})
    totales = [sum(f['valores'][i] for f in filas) for i in range(len(CONCEPTOS))]
    total = sum(totales)
    maximo = max([f['total'] for f in filas] + [Decimal('1')])
    for f in filas:
        f['ancho'] = round(float(f['total'] / maximo) * 100, 1) if f['total'] else 0

    pendientes = Pago.objects.filter(estado='Pendiente')
    hoy = timezone.localdate()
    return {
        'anio': anio,
        'conceptos': [_(t) for _c, t, _p in CONCEPTOS],
        'filas': filas,
        'totales': totales,
        'total': total,
        'por_cobrar': pendientes.aggregate(t=Sum('valor'))['t'] or 0,
        'vencido': pendientes.filter(fecha_vencimiento__lt=hoy).aggregate(t=Sum('valor'))['t'] or 0,
    }


def a_csv(datos):
    """CSV con punto y coma y BOM: Excel en español lo abre con columnas y tildes correctas."""
    salida = StringIO()
    salida.write('﻿')
    escritor = csv.writer(salida, delimiter=';')
    escritor.writerow([_('Recaudo %(anio)s · Conjunto Reserva de Madrid') % {'anio': datos['anio']}])
    escritor.writerow([_('Mes')] + datos['conceptos'] + [_('Total')])
    for f in datos['filas']:
        escritor.writerow([f['nombre']] + [int(v) for v in f['valores']] + [int(f['total'])])
    escritor.writerow([_('Total')] + [int(v) for v in datos['totales']] + [int(datos['total'])])
    escritor.writerow([])
    escritor.writerow([_('Por cobrar hoy'), int(datos['por_cobrar'])])
    escritor.writerow([_('De eso, vencido'), int(datos['vencido'])])
    return salida.getvalue()


def a_pdf(datos):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title=_('Recaudo %(anio)s') % {'anio': datos['anio']})
    estilos = getSampleStyleSheet()
    morado = colors.HexColor('#4C1D95')
    h = [
        Paragraph(f'<font color="#4C1D95"><b>{_("Reporte de recaudo")} {datos["anio"]}</b></font>', estilos['Title']),
        Paragraph(_('Conjunto Reserva de Madrid · generado el %(fecha)s')
                  % {'fecha': timezone.localtime().strftime('%d/%m/%Y %I:%M %p')}, estilos['Normal']),
        Spacer(1, 12),
    ]
    filas = [[_('Mes')] + datos['conceptos'] + [_('Total')]]
    for f in datos['filas']:
        filas.append([f['nombre']] + [pesos(v) if v else '—' for v in f['valores']] + [pesos(f['total'])])
    filas.append([_('Total')] + [pesos(v) for v in datos['totales']] + [pesos(datos['total'])])
    tabla = Table(filas, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (-1, 0), (-1, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FE')), ('TEXTCOLOR', (0, 0), (-1, 0), morado),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F7F5FC')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDD8EC')),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    h += [tabla, Spacer(1, 12), Paragraph(
        _('Por cobrar hoy: <b>%(pendiente)s</b> (de eso, vencido: %(vencido)s). Las facturas cuentan en el mes en '
          'que se pagaron; el parqueadero de visitantes, en el mes en que salió el vehículo.')
        % {'pendiente': pesos(datos['por_cobrar']), 'vencido': pesos(datos['vencido'])}, estilos['Normal'])]
    doc.build(h)
    return buffer.getvalue()

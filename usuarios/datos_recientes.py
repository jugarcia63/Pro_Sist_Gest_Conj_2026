"""Datos de ejemplo que dependen de la fecha: visitas, parqueos, paquetes, reservas, pagos, reportes,
avisos y movimientos del inventario. Todo se calcula desde HOY, así que al volver a generarlos el
conjunto se ve "al día": las facturas viejas están pagadas (salvo una cartera morosa a propósito),
los reportes antiguos están cerrados y las reservas pendientes son futuras.

Lo usan:
  - poblar_datos, la primera vez que carga el conjunto de ejemplo.
  - refrescar_datos, que borra estos datos y los vuelve a generar con fechas de hoy.

Necesita que ya existan las unidades, zonas, residentes y vigilantes de poblar_datos. Si falta alguno
(p. ej. en una base con datos propios), lo que depende de él simplemente se omite.
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from avisos.models import Aviso
from pagos.models import Pago
from paquetes.models import Paquete
from parqueadero.models import ParqueoVisitante, TarifaParqueadero, calcular_cobro
from reportes.models import ReporteDano
from reservas.datos_iniciales import ZONAS as INVENTARIO_BASE, _clave
from reservas.models import ItemEntregado, ItemInventario, MovimientoInventario, Reservas, ZonasComunes
from residentes.models import Residentes, Unidades
from usuarios.models import Usuario
from visitantes.models import Visitantes

USUARIO_PRUEBA = 'jvila69'
MARCA_RESERVA_PRUEBA = 'Reserva de prueba'
PAQUETES_PRUEBA = [
    # (guía, transportadora, descripción, horas atrás que llegó, entregado a o None si sigue en portería)
    ('PRB700045981', 'Servientrega', 'Caja mediana', 2, None),
    ('PRBMLC775102', 'Mercado Libre', 'Sobre', 9, None),
    ('PRBCOO240377', 'Coordinadora', 'Caja grande', 26, None),
    ('PRBAMZ553190', 'Amazon', 'Caja pequeña', 72, 'Juan Esteban Vila'),
    ('PRBINT889014', 'Interrapidísimo', 'Bolsa', 120, 'Familiar en portería'),
]

MESES_DE_HISTORIA = 6          # facturas de administración desde hace 5 meses hasta el actual
DIA_LIMITE_ADMINISTRACION = 10
CUOTA_PARQUEADERO = Decimal('85000')

# Documentos de los residentes de ejemplo (ver poblar_datos.RESIDENTES)
LAURA, ANDRES, CAMILA, SANTIAGO, VALENTINA, MATEO, DANIELA, SEBASTIAN, NATALIA, FELIPE = (
    f'10203040{n:02d}' for n in range(1, 11))
MOROSO = SEBASTIAN        # debe los últimos meses: así la cartera vencida tiene un caso real
ATRASADO = SANTIAGO       # olvidó pagar el mes pasado


class _Contexto:
    """Reúne lo que ya existe en la base y las utilidades de fecha."""

    def __init__(self):
        self.ahora = timezone.now()
        self.hoy = timezone.localdate()
        self.tz = timezone.get_current_timezone()
        self.residentes = {r.num_documento: r for r in Residentes.objects.select_related('id_unidad_fk', 'usuario')}
        self.vigilantes = list(Usuario.objects.filter(rol='seguridad', is_active=True).order_by('pk')) or [None]
        self.admin = Usuario.objects.filter(rol='admin', is_active=True).order_by('pk').first()
        self.zonas = {z.nombre: z for z in ZonasComunes.objects.all()}

    def momento(self, dias, hora, minuto=0):
        """Fecha y hora local a 'dias' de hoy (negativo = pasado)."""
        return timezone.make_aware(datetime.combine(self.hoy + timedelta(days=dias), time(hora, minuto)), self.tz)

    def vigilante(self, i):
        return self.vigilantes[i % len(self.vigilantes)]

    def r(self, documento):
        return self.residentes.get(documento)

    def mes(self, desplazamiento):
        """Primer día del mes a 'desplazamiento' meses del actual (0 = este mes)."""
        anio, mes = self.hoy.year, self.hoy.month + desplazamiento
        while mes < 1:
            anio, mes = anio - 1, mes + 12
        while mes > 12:
            anio, mes = anio + 1, mes - 12
        return self.hoy.replace(year=anio, month=mes, day=1)


def borrar():
    """Borra todo lo que depende de la fecha. No toca usuarios, residentes, unidades, zonas ni vehículos."""
    ParqueoVisitante.objects.all().delete()
    Visitantes.objects.all().delete()
    Paquete.objects.all().delete()
    Pago.objects.all().delete()
    MovimientoInventario.objects.all().delete()
    ItemEntregado.objects.all().delete()
    Reservas.objects.all().delete()
    ReporteDano.objects.all().delete()
    Aviso.objects.all().delete()
    _inventario_completo()


def _inventario_completo():
    """Deja el inventario como recién comprado: cantidades de la lista base y nada en reparación."""
    base = {(_clave(zona), _clave(nombre)): cantidad
            for zona, (_h, _l, _v, items) in INVENTARIO_BASE.items() for nombre, cantidad, _valor in items}
    for item in ItemInventario.objects.select_related('zona'):
        item.cantidad = base.get((_clave(item.zona.nombre), _clave(item.nombre)), item.cantidad)
        item.fuera_servicio = 0
        item.save(update_fields=['cantidad', 'fuera_servicio'])


def generar():
    """Crea los datos con fechas de hoy. Devuelve un resumen {modelo: cantidad}."""
    c = _Contexto()
    _visitas_y_parqueos(c)
    _paquetes(c)
    reservas = _reservas(c)
    _pagos(c)
    _reportes(c)
    _avisos(c, reservas)
    paquetes_de_prueba(USUARIO_PRUEBA)
    reservas_de_prueba(USUARIO_PRUEBA)
    return {
        'visitas': Visitantes.objects.count(), 'parqueos': ParqueoVisitante.objects.count(),
        'paquetes': Paquete.objects.count(), 'reservas': Reservas.objects.count(),
        'pagos': Pago.objects.count(), 'reportes': ReporteDano.objects.count(),
        'movimientos de inventario': MovimientoInventario.objects.count(),
    }


# ---------- portería ----------

def _visitas_y_parqueos(c):
    # (nombre, apellidos, cédula, residente, horas atrás, placa del carro o None)
    visitas = [
        ('Carlos', 'Díaz Molina', '79451230', LAURA, 1.5, 'DFG234'),
        ('Andrea', 'Suárez Pinto', '1032456789', VALENTINA, 0.3, None),
        ('Martha', 'Lucía Pérez', '51876345', DANIELA, 3, 'KLM78E'),
        ('Jorge', 'Ríos Castaño', '80123456', ANDRES, 7, 'TUV561'),
        ('Sofía', 'Navarro León', '1019876543', CAMILA, 22, 'NBV902'),
        ('Hernán', 'Acosta Ruiz', '79654321', NATALIA, 27, None),
        ('Gloria', 'Patiño Vera', '41234567', FELIPE, 48, 'WER33H'),
        ('Felipe', 'Cárdenas Mora', '1001234567', MATEO, 50, None),
        ('Diana', 'Rueda Salcedo', '52789012', LAURA, 73, None),
        ('Ricardo', 'Montoya Gil', '79012345', SEBASTIAN, 75, 'GHJ482'),
    ]
    tarifa = TarifaParqueadero.vigente()
    # Cuánto se quedaron los carros que ya salieron (minutos); None = sigue adentro
    estadias = {'DFG234': None, 'KLM78E': None, 'TUV561': 95, 'NBV902': 200, 'WER33H': 250, 'GHJ482': 130}
    for i, (nombre, apellidos, cedula, documento, horas, placa) in enumerate(visitas):
        residente = c.r(documento)
        if residente is None:
            continue
        ingreso = c.ahora - timedelta(hours=horas)
        visita = Visitantes.objects.create(
            nombre=nombre, apellidos=apellidos, tipo_documento='CC', num_documento=cedula,
            id_residente_fk=residente, id_unidad_fk=residente.id_unidad_fk, fecha_ingreso=ingreso,
            autorizado_por=c.vigilante(i),
        )
        if not placa or residente.id_unidad_fk is None:
            continue
        parqueo = ParqueoVisitante(
            placa=placa, tipo_vehiculo='Moto' if placa[-1].isalpha() else 'Carro',
            id_unidad_fk=residente.id_unidad_fk, conductor=f'{nombre} {apellidos}', visitante=visita,
            fecha_ingreso=ingreso + timedelta(minutes=2), valor_hora=tarifa.valor_hora,
            horas_gratis=tarifa.horas_gratis, registrado_por=c.vigilante(i),
        )
        minutos = estadias.get(placa)
        if minutos:
            parqueo.fecha_salida = parqueo.fecha_ingreso + timedelta(minutes=minutos)
            _, parqueo.horas_cobradas, parqueo.valor_cobrado = calcular_cobro(
                parqueo.fecha_ingreso, parqueo.fecha_salida, tarifa.valor_hora, tarifa.horas_gratis)
            parqueo.estado = 'Salió'
            parqueo.salida_por = c.vigilante(i + 1)
        parqueo.save()


def _paquetes(c):
    # (guía, transportadora, residente, descripción, horas atrás que llegó, entregado a o None)
    datos = [
        ('700045123987', 'Servientrega', LAURA, 'Caja mediana', 2, None),
        ('MLC2026118843', 'Mercado Libre', LAURA, 'Sobre', 20, None),
        ('240198776', 'Coordinadora', VALENTINA, 'Caja grande', 5, None),
        ('TCC88120045', 'TCC', MATEO, '', 1, None),
        ('INT5523001', 'Interrapidísimo', ANDRES, 'Bolsa', 30, 'Andrés Pardo Salazar'),
        ('AMZ114477', 'Amazon', NATALIA, 'Caja pequeña', 52, 'Carolina Vargas'),
        ('DHL6650321', 'DHL', DANIELA, 'Sobre de documentos', 76, 'Daniela Castro Ospina'),
        ('SRV700049921', 'Servientrega', FELIPE, 'Caja mediana', 100, 'Felipe Ramírez Arango'),
    ]
    for i, (guia, empresa, documento, descripcion, horas, entregado_a) in enumerate(datos):
        residente = c.r(documento)
        if residente is None or residente.id_unidad_fk is None:
            continue
        recepcion = c.ahora - timedelta(hours=horas)
        paquete = Paquete(numero_guia=guia, empresa=empresa, destinatario=str(residente),
                          id_unidad_fk=residente.id_unidad_fk, descripcion=descripcion,
                          fecha_recepcion=recepcion, recibido_por=c.vigilante(i))
        if entregado_a:
            paquete.estado = 'Entregado'
            paquete.fecha_entrega = recepcion + timedelta(hours=4)
            paquete.entregado_a = entregado_a
            paquete.entregado_por = c.vigilante(i + 1)
        paquete.save()


# ---------- reservas, entregas e inventario ----------

def _crear_reserva(c, zona, residente, dias, hora, horas, estado, observaciones='', limpieza=False, pedida=7):
    zona = c.zonas.get(zona)
    if zona is None or residente is None or residente.id_unidad_fk is None:
        return None
    inicio = c.momento(dias, hora)
    reserva = Reservas(
        id_zona_fk=zona, id_unidad_fk=residente.id_unidad_fk, reservado_por=residente.usuario,
        fecha_reserva=inicio - timedelta(days=pedida), fecha_inicio=inicio, fecha_fin=inicio + timedelta(hours=horas),
        estado=estado, observaciones=observaciones, incluye_limpieza=limpieza,
    )
    reserva.calcular_cobro()
    reserva.save()
    return reserva


def _factura_reserva(c, reserva, pagada):
    """Factura del uso de la zona (solo zonas con costo). Se vence el día del uso."""
    if not reserva or not reserva.valor_total:
        return
    residente = reserva.reservado_por.residente if reserva.reservado_por_id else None
    uso = timezone.localtime(reserva.fecha_inicio)
    Pago.objects.create(
        id_residente_fk=residente, id_reserva_fk=reserva, tipo_pago='Reserva', valor=reserva.valor_total,
        mes_ano=uso.replace(day=1, hour=0, minute=0, second=0, microsecond=0), fecha_vencimiento=uso.date(),
        estado='Pagado' if pagada else 'Pendiente',
        fecha_pago=min((uso - timedelta(days=2)).date(), c.hoy) if pagada else None,
        metodo_pago='Tarjeta •••• 4242' if pagada else None,
    )


def _entregar(c, reserva, novedades=None, limpia=True, nota='', multa_pagada=False, i=0):
    """Recibe la zona como lo haría portería: revisa implementos, mueve el inventario y crea la multa."""
    if reserva is None:
        return None
    novedades = novedades or {}  # {nombre del implemento: (faltan, dañados)}
    cuando = reserva.fecha_fin + timedelta(minutes=25)
    vigilante = c.vigilante(i)
    texto = f'Entrega de la reserva #{reserva.pk} ({reserva.id_unidad_fk})'
    total = Decimal('0')
    for item in reserva.id_zona_fk.inventario.all():
        faltan, danados = novedades.get(item.nombre, (0, 0))
        entregado = ItemEntregado.objects.create(
            reserva=reserva, item=item, nombre=item.nombre, cantidad_prestada=item.disponibles,
            faltantes=faltan, danados=danados, valor_reposicion=item.valor_reposicion)
        total += entregado.cargo
        MovimientoInventario.registrar(item, MovimientoInventario.PERDIDA, faltan, vigilante, reserva, texto, cuando)
        MovimientoInventario.registrar(item, MovimientoInventario.DANO, danados, vigilante, reserva, texto, cuando)
    zona = reserva.id_zona_fk
    if not limpia and not reserva.incluye_limpieza and zona.ofrece_limpieza:
        total += zona.valor_limpieza
    reserva.fecha_entrega, reserva.recibida_por = cuando, vigilante
    reserva.zona_limpia = None if reserva.incluye_limpieza else limpia
    reserva.valor_multa, reserva.observaciones_entrega, reserva.estado = total, nota, 'Finalizada'
    reserva.save()
    if total:
        residente = reserva.reservado_por.residente if reserva.reservado_por_id else None
        local = timezone.localtime(cuando)
        vence = local.date() + timedelta(days=15)
        Pago.objects.create(
            id_residente_fk=residente, id_reserva_fk=reserva, tipo_pago='Multa', valor=total,
            mes_ano=local.replace(day=1, hour=0, minute=0, second=0, microsecond=0), fecha_vencimiento=vence,
            estado='Pagado' if multa_pagada else 'Pendiente',
            fecha_pago=(local + timedelta(days=6)).date() if multa_pagada else None,
            metodo_pago='Tarjeta •••• 4242' if multa_pagada else None,
        )
    return reserva


def _movimiento_admin(c, zona, nombre, tipo, cantidad, dias, nota):
    item = ItemInventario.objects.filter(zona__nombre=zona, nombre=nombre).first()
    if item:
        MovimientoInventario.registrar(item, tipo, cantidad, c.admin, nota=nota, fecha=c.momento(dias, 10))


def _reservas(c):
    r = c.r
    M = MovimientoInventario
    creadas = {}

    # --- Ya usadas y recibidas por portería ---
    salon_1 = _crear_reserva(c, 'Salón social', r(LAURA), -40, 15, 6, 'Aprobada', 'Cumpleaños de mi hija, 35 invitados', True)
    _factura_reserva(c, salon_1, pagada=True)
    _entregar(c, salon_1, i=0)

    bbq_1 = _crear_reserva(c, 'Zona BBQ', r(ANDRES), -26, 12, 4, 'Aprobada', 'Asado de fin de mes')
    _factura_reserva(c, bbq_1, pagada=True)
    _entregar(c, bbq_1, {'Pinzas para asar': (1, 0), 'Sillas': (0, 2)}, limpia=False,
              nota='Faltó una pinza, dos sillas con la pata partida y la parrilla quedó sucia.', multa_pagada=True, i=1)
    # La administración arregló las sillas y repuso la pinza con lo que se cobró de multa
    _movimiento_admin(c, 'Zona BBQ', 'Sillas', M.REPARADO, 2, -20, 'Se cambiaron las patas en la carpintería.')
    _movimiento_admin(c, 'Zona BBQ', 'Pinzas para asar', M.COMPRA, 1, -18, 'Reposición pagada con la multa.')

    _entregar(c, _crear_reserva(c, 'Piscina', r(VALENTINA), -19, 10, 3, 'Aprobada', 'Clase de natación de los niños'), i=2)

    juegos = _crear_reserva(c, 'Salón de juegos', r(NATALIA), -12, 16, 3, 'Aprobada', 'Torneo de billar')
    _entregar(c, juegos, {'Tacos de billar': (0, 1)}, nota='Un taco llegó con la punta despegada.', i=0)

    _entregar(c, _crear_reserva(c, 'Cancha múltiple', r(MATEO), -8, 18, 2, 'Aprobada', 'Partido de microfútbol'), i=1)

    salon_2 = _crear_reserva(c, 'Salón social', r(DANIELA), -5, 18, 5, 'Aprobada', 'Despedida de compañera de trabajo', True)
    _factura_reserva(c, salon_2, pagada=True)
    _entregar(c, salon_2, {'Vajilla (puesto completo)': (2, 0)}, nota='Faltaron dos puestos de vajilla.', i=2)

    # Novedades encontradas por la administración fuera de las reservas
    _movimiento_admin(c, 'Piscina', 'Flotadores', M.DANO, 1, -30, 'Pinchado.')
    _movimiento_admin(c, 'Piscina', 'Flotadores', M.BAJA, 1, -28, 'No se pudo parchar.')
    _movimiento_admin(c, 'Gimnasio', 'Colchonetas', M.DANO, 1, -6, 'Rota en la costura; se envió a tapicería.')

    # --- No se usaron ---
    _crear_reserva(c, 'Gimnasio', r(CAMILA), -15, 7, 1, 'Cancelada', '')
    _crear_reserva(c, 'Zona BBQ', r(FELIPE), -10, 13, 4, 'Rechazada', 'Ese día había mantenimiento de la parrilla')
    _crear_reserva(c, 'Cancha múltiple', r(SANTIAGO), -3, 17, 2, 'Vencida', 'Entrenamiento', pedida=4)

    # --- Terminó ayer: portería debe recibir la zona ---
    creadas['por_recibir'] = _crear_reserva(c, 'Salón de juegos', r(FELIPE), -1, 15, 3, 'Aprobada', 'Tarde de juegos de mesa')

    # --- Próximas ---
    salon_3 = _crear_reserva(c, 'Salón social', r(LAURA), 3, 15, 6, 'Aprobada', 'Primera comunión, 40 invitados', True)
    _factura_reserva(c, salon_3, pagada=False)
    creadas['aprobada'] = salon_3
    _crear_reserva(c, 'Zona BBQ', r(ANDRES), 5, 12, 4, 'Pendiente', 'Asado familiar', pedida=2)
    _crear_reserva(c, 'Piscina', r(VALENTINA), 2, 10, 3, 'Aprobada', '')
    _crear_reserva(c, 'Cancha múltiple', r(MATEO), 1, 18, 2, 'Pendiente', 'Partido con los vecinos de la torre C', pedida=1)
    _crear_reserva(c, 'Salón social', r(DANIELA), 10, 18, 5, 'Pendiente', 'Reunión de copropietarios de la torre B', pedida=3)
    _crear_reserva(c, 'Salón de juegos', r(NATALIA), 4, 16, 3, 'Aprobada', '')
    _crear_reserva(c, 'Gimnasio', r(CAMILA), 6, 7, 1, 'Cancelada', '')
    bbq_2 = _crear_reserva(c, 'Zona BBQ', r(FELIPE), 8, 13, 4, 'Aprobada', 'Cumpleaños de mi papá', True)
    _factura_reserva(c, bbq_2, pagada=True)
    creadas['multa'] = juegos
    return creadas


# ---------- pagos ----------

def _pagos(c):
    """Administración por unidad y parqueadero de residentes, de los últimos meses hasta el actual."""
    from vehiculos.models import Vehiculos

    # Una factura por unidad, a nombre del primer residente registrado
    titulares = {}
    for residente in sorted(c.residentes.values(), key=lambda x: x.pk):
        if residente.id_unidad_fk_id and residente.id_unidad_fk_id not in titulares:
            titulares[residente.id_unidad_fk_id] = residente
    con_carro = set(Vehiculos.objects.filter(tipo_vehiculo='Carro').values_list('id_residente_fk_id', flat=True))

    for desplazamiento in range(-(MESES_DE_HISTORIA - 1), 1):
        inicio_mes = c.mes(desplazamiento)
        vence = inicio_mes.replace(day=DIA_LIMITE_ADMINISTRACION)
        mes_ano = timezone.make_aware(datetime.combine(inicio_mes, time(0)), c.tz)
        for i, residente in enumerate(titulares.values()):
            pagado, fecha_pago = _estado_cuota(c, residente, desplazamiento, inicio_mes, vence, i)
            metodo = (f'Tarjeta •••• {4242 + i * 7 % 1000:04d}' if i % 3 else 'Transferencia PSE') if pagado else None
            comunes = dict(id_residente_fk=residente, mes_ano=mes_ano, fecha_vencimiento=vence,
                           estado='Pagado' if pagado else 'Pendiente', fecha_pago=fecha_pago, metodo_pago=metodo)
            Pago.objects.create(tipo_pago='Administración', valor=_cuota(residente.id_unidad_fk), **comunes)
            if residente.pk in con_carro:
                Pago.objects.create(tipo_pago='Parqueadero', valor=CUOTA_PARQUEADERO, **comunes)

    # Una multa vieja, ya pagada, por ruido después de las 10 p. m.
    sebastian = c.r(SEBASTIAN)
    if sebastian:
        fecha = c.hoy - timedelta(days=50)
        Pago.objects.create(id_residente_fk=sebastian, tipo_pago='Multa', valor=Decimal('150000'),
                            mes_ano=timezone.make_aware(datetime.combine(fecha.replace(day=1), time(0)), c.tz),
                            fecha_vencimiento=fecha + timedelta(days=15), estado='Pagado',
                            fecha_pago=fecha + timedelta(days=9), metodo_pago='Transferencia PSE')


def _estado_cuota(c, residente, desplazamiento, inicio_mes, vence, i):
    """Devuelve (pagado, fecha de pago). Casi todos pagan a tiempo; hay un moroso y un atrasado a propósito."""
    if residente.num_documento == MOROSO and desplazamiento >= -2:
        return False, None
    if residente.num_documento == ATRASADO and desplazamiento == -1:
        return False, None
    if desplazamiento < 0:
        # Unos pagan antes del día 10 y unos pocos un par de días tarde
        dia = 2 + (i * 3) % 8 if i % 5 else 13
        return True, inicio_mes.replace(day=dia)
    # Mes actual: antes del día límite solo algunos han pagado; después, casi todos
    if c.hoy < vence:
        if i % 3 == 0:
            return True, min(c.hoy, inicio_mes + timedelta(days=i % 3))
        return False, None
    if i % 4 == 1:
        return False, None
    return True, inicio_mes.replace(day=min(2 + i % 8, c.hoy.day))


def _cuota(unidad):
    return Decimal('340000') if unidad and unidad.area and unidad.area > 60 else Decimal('285000')


# ---------- reportes de daños ----------

def _reportes(c):
    r = c.r
    # (residente, categoría, descripción, estado, días atrás, días que tardó en resolverse)
    datos = [
        (r(LAURA), 'Plomería', 'Gotera en el techo del baño principal desde anoche.', 'Abierto', 1, None),
        (r(MATEO), 'Ascensor', 'El ascensor de la torre B hace un ruido fuerte al frenar en el piso 3.', 'Abierto', 2, None),
        (r(CAMILA), 'Estructural', 'Apareció humedad en la pared de la habitación que da al patio.', 'Abierto', 3, None),
        (r(ANDRES), 'Eléctrico', 'La luz del pasillo del piso 2 está intermitente.', 'En proceso', 4, None),
        (r(NATALIA), 'Seguridad', 'El citófono del apartamento no timbra cuando llaman de portería.', 'En proceso', 6, None),
        (r(DANIELA), 'Otro', 'La puerta del shut de basuras de la torre B no cierra bien.', 'En proceso', 9, None),
        (r(VALENTINA), 'Zonas comunes', 'Una de las sillas plegables del salón social está rota.', 'Cerrado', 15, 3),
        (r(FELIPE), 'Plomería', 'La llave del lavaplatos gotea constantemente.', 'Cerrado', 25, 2),
        (r(SANTIAGO), 'Eléctrico', 'Se quemó el bombillo de la entrada de la torre A.', 'Cerrado', 40, 1),
        (r(LAURA), 'Zonas comunes', 'La malla de la cancha tiene un hueco en la esquina norte.', 'Cerrado', 62, 8),
    ]
    for residente, categoria, descripcion, estado, dias, tardo in datos:
        if residente is None or residente.id_unidad_fk is None:
            continue
        fecha = c.ahora - timedelta(days=dias, hours=dias % 5 + 1)
        reporte = ReporteDano.objects.create(
            id_residente_fk=residente, categoria=categoria, descripcion=descripcion,
            torre=residente.id_unidad_fk.torre, piso=residente.id_unidad_fk.piso, estado=estado,
            fecha_resolucion=fecha + timedelta(days=tardo) if tardo else None,
        )
        # fecha_reporte es auto_now_add: se ajusta después para que tenga su antigüedad
        ReporteDano.objects.filter(pk=reporte.pk).update(fecha_reporte=fecha)


# ---------- avisos ----------

def _avisos(c, reservas):
    """Algunos avisos recientes en la campana de los residentes (sin enviar correos)."""
    avisos = []

    def aviso(residente, tipo, titulo, mensaje, url, horas, leido=False):
        if residente and residente.usuario_id:
            avisos.append((Aviso.objects.create(usuario=residente.usuario, tipo=tipo, titulo=titulo, mensaje=mensaje,
                                                url=url, leido=leido), horas))

    laura = c.r(LAURA)
    salon = reservas.get('aprobada')
    if salon:
        inicio = timezone.localtime(salon.fecha_inicio)
        aviso(laura, 'reserva', 'Tu reserva fue aprobada',
              f'Salón social el {inicio:%d/%m/%Y} de {inicio:%H:%M} a {timezone.localtime(salon.fecha_fin):%H:%M}. '
              'La factura está en Mis pagos.', reverse('lista_reservas'), 30)
    aviso(laura, 'paquete', 'Llegó un paquete para ti', 'Servientrega · guía 700045123987. Recógelo en portería.',
          reverse('mis_paquetes'), 2)
    aviso(c.r(VALENTINA), 'paquete', 'Llegó un paquete para ti', 'Coordinadora · guía 240198776. Recógelo en portería.',
          reverse('mis_paquetes'), 5)
    juegos = reservas.get('multa')
    if juegos:
        aviso(c.r(NATALIA), 'multa', 'Tienes una multa',
              '$70.000 por la entrega del Salón de juegos: un taco de billar dañado.', reverse('lista_pagos_residente'),
              24 * 12 - 4, leido=True)
    aviso(c.r(SEBASTIAN), 'factura', 'Tienes facturas vencidas',
          'Tu cuota de administración tiene meses sin pagar. Ponte al día en Mis pagos.',
          reverse('lista_pagos_residente'), 20)
    for creado, horas in avisos:
        Aviso.objects.filter(pk=creado.pk).update(creado=c.ahora - timedelta(hours=horas))


# ---------- residente de pruebas (jvila69) ----------

def paquetes_de_prueba(username):
    """Paquetes para el residente de pruebas. Se crean una sola vez (no se duplican)."""
    residente = Residentes.objects.select_related('id_unidad_fk').filter(usuario__username__iexact=username).first()
    if residente is None or residente.id_unidad_fk is None:
        return False
    if Paquete.objects.filter(numero_guia__in=[g for g, *_ in PAQUETES_PRUEBA]).exists():
        return False
    ahora = timezone.now()
    vigilantes = list(Usuario.objects.filter(rol='seguridad', is_active=True).order_by('pk')[:2]) or [None]
    destinatario = f"{residente.nombres or ''} {residente.apellidos or ''}".strip() or username
    for i, (guia, empresa, descripcion, horas, entregado_a) in enumerate(PAQUETES_PRUEBA):
        recepcion = ahora - timedelta(hours=horas)
        paquete = Paquete(numero_guia=guia, empresa=empresa, destinatario=destinatario,
                          id_unidad_fk=residente.id_unidad_fk, descripcion=descripcion,
                          fecha_recepcion=recepcion, recibido_por=vigilantes[i % len(vigilantes)])
        if entregado_a:
            paquete.estado = 'Entregado'
            paquete.fecha_entrega = recepcion + timedelta(hours=3)
            paquete.entregado_a = entregado_a
            paquete.entregado_por = vigilantes[(i + 1) % len(vigilantes)]
        paquete.save()
    return True


def reservas_de_prueba(username):
    """Dos reservas para el residente de pruebas: una de ayer lista para recibir (con inventario por
    revisar) y una próxima ya aprobada con su factura. Se crean una sola vez."""
    from reservas.cobros import sincronizar_factura

    residente = (Residentes.objects.select_related('id_unidad_fk', 'usuario')
                 .filter(usuario__username__iexact=username).first())
    if residente is None or residente.id_unidad_fk is None:
        return False
    if Reservas.objects.filter(observaciones__startswith=MARCA_RESERVA_PRUEBA).exists():
        return False
    bbq = ZonasComunes.objects.filter(nombre='Zona BBQ').first()
    salon = ZonasComunes.objects.filter(nombre='Salón social').first()
    if not bbq or not salon:
        return False
    c = _Contexto()
    for zona, dias, hora, horas, limpieza, nota in (
        (bbq, -1, 13, 4, False, 'asado familiar'),
        (salon, 6, 16, 5, True, 'cumpleaños, 30 invitados'),
    ):
        reserva = Reservas(
            id_zona_fk=zona, id_unidad_fk=residente.id_unidad_fk, reservado_por=residente.usuario,
            fecha_reserva=timezone.now() - timedelta(days=3), fecha_inicio=c.momento(dias, hora),
            fecha_fin=c.momento(dias, hora + horas), estado='Aprobada', incluye_limpieza=limpieza,
            observaciones=f'{MARCA_RESERVA_PRUEBA}: {nota}',
        )
        reserva.calcular_cobro()
        reserva.save()
        sincronizar_factura(reserva)
    return True

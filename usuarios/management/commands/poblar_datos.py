"""Llena la base con datos de ejemplo que tienen sentido entre sí:
torres y apartamentos, zonas comunes, residentes con su cuenta, personal de seguridad,
vehículos, visitas, reservas, facturas y reportes de daños.

    python manage.py poblar_datos

Es seguro ejecutarlo varias veces: si los datos de ejemplo ya existen, no los duplica.
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pagos.models import Pago
from reportes.models import ReporteDano
from reservas.models import Reservas, ZonasComunes
from residentes.models import Residentes, Unidades
from usuarios.models import Usuario
from vehiculos.models import Vehiculos
from visitantes.models import Visitantes

CLAVE_RESIDENTES = 'Conjunto2026'
CLAVE_SEGURIDAD = 'Porteria2026'
CLAVE_JUAN = '123456789'

TORRES = ['A', 'B', 'C']
PISOS = range(1, 6)        # 5 pisos por torre
APTOS_POR_PISO = (1, 2)    # 101, 102, 201, 202...

ZONAS = [
    ('Salón social', 60, 'Salón con cocina, 10 mesas, sillas y sonido.',
     'Horario: 8:00 a.m. a 11:00 p.m.\nMúsica a volumen moderado después de las 10:00 p.m.\nEntregar el salón limpio.'),
    ('Zona BBQ', 20, 'Parrilla a gas con terraza cubierta y mesón.',
     'Traer su propio carbón o pipeta.\nLimpiar la parrilla al terminar.'),
    ('Piscina', 30, 'Piscina para adultos y niños con zona húmeda.',
     'Horario: 9:00 a.m. a 7:00 p.m.\nNiños siempre acompañados.\nDucharse antes de entrar.'),
    ('Gimnasio', 12, 'Máquinas de cardio, pesas y colchonetas.',
     'Usar toalla.\nMáximo 1 hora por persona cuando hay fila.'),
    ('Cancha múltiple', 14, 'Microfútbol y baloncesto con iluminación nocturna.',
     'Horario: 7:00 a.m. a 9:00 p.m.\nUsar calzado deportivo.'),
    ('Parque infantil', 25, 'Columpios, rodadero y arenero.', 'Para niños menores de 12 años.'),
    ('Salón de juegos', 15, 'Mesa de billar, ping-pong y juegos de mesa.', 'Menores de 14 años con un adulto.'),
]

# (nombres, apellidos, documento, teléfono, torre, apto, usuario o None si aún no ha creado su cuenta)
RESIDENTES = [
    ('Laura', 'Gómez Restrepo', '1020304001', '3104567801', 'A', '101', 'laura.gomez'),
    ('Andrés', 'Pardo Salazar', '1020304002', '3114567802', 'A', '202', 'andres.pardo'),
    ('Camila', 'Torres Mejía', '1020304003', '3124567803', 'A', '301', 'camila.torres'),
    ('Santiago', 'López Duarte', '1020304004', '3134567804', 'A', '502', 'santiago.lopez'),
    ('Valentina', 'Rojas Cárdenas', '1020304005', '3144567805', 'B', '102', 'valentina.rojas'),
    ('Mateo', 'Herrera Quintero', '1020304006', '3154567806', 'B', '201', 'mateo.herrera'),
    ('Daniela', 'Castro Ospina', '1020304007', '3164567807', 'B', '402', 'daniela.castro'),
    ('Sebastián', 'Moreno Vélez', '1020304008', '3174567808', 'B', '501', 'sebastian.moreno'),
    ('Natalia', 'Vargas Pineda', '1020304009', '3184567809', 'C', '101', 'natalia.vargas'),
    ('Felipe', 'Ramírez Arango', '1020304010', '3194567810', 'C', '202', 'felipe.ramirez'),
    ('Mariana', 'Ortiz Bernal', '1020304011', '3204567811', 'C', '302', None),
    ('Julián', 'Suárez Rincón', '1020304012', '3214567812', 'C', '401', None),
    ('Paula', 'Mendoza Giraldo', '1020304013', '3224567813', 'A', '401', None),
]

GUARDIAS = [
    ('Carlos', 'Mejía Rodríguez', 'carlos.mejia'),
    ('Óscar', 'Peña Galvis', 'oscar.pena'),
    ('Luz Marina', 'Cortés Ávila', 'luz.cortes'),
]

# (documento del dueño, placa, tipo, marca, modelo, color)
VEHICULOS = [
    ('1020304001', 'JKL482', 'Carro', 'Mazda', 'CX-30 2022', 'Rojo'),
    ('1020304001', 'QWE45F', 'Moto', 'Yamaha', 'FZ 2.0', 'Negro'),
    ('1020304002', 'GHT719', 'Carro', 'Renault', 'Duster 2021', 'Gris'),
    ('1020304003', 'MNP305', 'Carro', 'Kia', 'Picanto 2023', 'Blanco'),
    ('1020304005', 'BCD912', 'Carro', 'Chevrolet', 'Onix 2022', 'Azul'),
    ('1020304006', 'RTY88K', 'Moto', 'AKT', 'NKD 125', 'Rojo'),
    ('1020304007', 'XYZ227', 'Carro', 'Toyota', 'Corolla Cross 2024', 'Plata'),
    ('1020304009', 'LMN654', 'Carro', 'Volkswagen', 'Gol 2019', 'Negro'),
    ('1020304010', 'PQR103', 'Carro', 'Nissan', 'Kicks 2023', 'Blanco'),
    ('1020304010', 'HJK21D', 'Moto', 'Honda', 'CB 190R', 'Azul'),
]


def _unidad_area(apto):
    return Decimal('72.40') if apto.endswith('1') else Decimal('58.75')


def _cuota(unidad):
    return Decimal('340000') if unidad.area and unidad.area > 60 else Decimal('285000')


class Command(BaseCommand):
    help = 'Carga datos de ejemplo relacionados (torres, zonas, residentes, vigilantes, pagos, etc.).'

    def handle(self, *args, **options):
        juan = self._asegurar_juan_garcia()

        if Usuario.objects.filter(username='laura.gomez').exists():
            self.stdout.write('Los datos de ejemplo ya estaban cargados; no se duplicó nada.')
            return

        with transaction.atomic():
            unidades = self._crear_unidades()
            zonas = self._crear_zonas()
            residentes = self._crear_residentes(unidades)
            guardias = self._crear_guardias()
            self._crear_vehiculos(residentes)
            self._crear_visitantes(residentes, guardias)
            reservas = self._crear_reservas(zonas, residentes)
            self._crear_pagos(residentes, reservas)
            self._crear_reportes(residentes)

        self.stdout.write(self.style.SUCCESS(
            f'Datos de ejemplo cargados: {len(unidades)} unidades, {len(zonas)} zonas comunes, '
            f'{len(residentes)} residentes y {len(guardias)} vigilantes.'
        ))
        self.stdout.write(f'  Administrador: {juan.username} / {CLAVE_JUAN}')
        self.stdout.write(f'  Residentes (ej. laura.gomez) / {CLAVE_RESIDENTES}')
        self.stdout.write(f'  Seguridad (ej. carlos.mejia) / {CLAVE_SEGURIDAD}')

    # ---------- piezas ----------

    def _asegurar_juan_garcia(self):
        juan = Usuario.objects.filter(username__iexact='Juan_Garcia').first()
        if juan is None:
            juan = Usuario.objects.create_user('Juan_Garcia', 'juan.garcia@conjunto.co', CLAVE_JUAN)
            self.stdout.write(f'Usuario Juan_Garcia creado con la contraseña {CLAVE_JUAN}.')
        juan.first_name, juan.last_name = 'Juan', 'García'
        juan.rol = 'admin'
        juan.is_staff = juan.is_superuser = juan.is_active = True
        juan.debe_cambiar_password = False
        juan.save()
        return juan

    def _crear_unidades(self):
        unidades = {}
        for torre in TORRES:
            for piso in PISOS:
                for n in APTOS_POR_PISO:
                    apto = f'{piso}0{n}'
                    unidad = Unidades.objects.filter(torre=torre, apto=apto).order_by('pk').first()                         or Unidades.objects.create(torre=torre, apto=apto, piso=piso, area=_unidad_area(apto), estado=1)
                    unidades[(torre, apto)] = unidad
        return unidades

    def _crear_zonas(self):
        zonas = {}
        for nombre, capacidad, descripcion, reglas in ZONAS:
            zona = ZonasComunes.objects.filter(nombre=nombre).order_by('pk').first()                 or ZonasComunes.objects.create(nombre=nombre, capacidad=capacidad, descripcion=descripcion,
                                               reglas=reglas, estado=1)
            zonas[nombre] = zona
        return zonas

    def _crear_residentes(self, unidades):
        ahora = timezone.now()
        residentes = {}
        for i, (nombres, apellidos, documento, telefono, torre, apto, username) in enumerate(RESIDENTES):
            correo = f"{(username or nombres.lower() + '.' + apellidos.split()[0].lower())}@correo.co"
            correo = correo.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            residente = Residentes.objects.filter(num_documento=documento).first()
            if residente is None:
                residente = Residentes.objects.create(
                    nombres=nombres, apellidos=apellidos, tipo_documento='CC', num_documento=documento,
                    telefono=telefono, email=correo, id_unidad_fk=unidades[(torre, apto)],
                    fecha_registro=ahora - timedelta(days=420 - i * 25), estado=1,
                )
            if username and not residente.usuario_id:
                usuario = Usuario.objects.create_user(username, correo, CLAVE_RESIDENTES,
                                                      first_name=nombres, last_name=apellidos)
                usuario.rol = 'residente'
                usuario.save(update_fields=['rol'])
                residente.usuario = usuario
                residente.save(update_fields=['usuario'])
            residentes[documento] = residente
        return residentes

    def _crear_guardias(self):
        guardias = []
        for nombres, apellidos, username in GUARDIAS:
            guardia = Usuario.objects.filter(username=username).first()
            if guardia is None:
                guardia = Usuario.objects.create_user(username, f'{username}@conjunto.co', CLAVE_SEGURIDAD,
                                                      first_name=nombres, last_name=apellidos)
                guardia.rol = 'seguridad'
                guardia.save(update_fields=['rol'])
            guardias.append(guardia)
        return guardias

    def _crear_vehiculos(self, residentes):
        for documento, placa, tipo, marca, modelo, color in VEHICULOS:
            if not Vehiculos.objects.filter(placa=placa).exists():
                Vehiculos.objects.create(placa=placa, tipo_vehiculo=tipo, marca=marca, modelo=modelo, color=color,
                                         id_residente_fk=residentes[documento], estado='Activo')

    def _crear_visitantes(self, residentes, guardias):
        ahora = timezone.now()
        r = residentes
        # (nombre, apellidos, documento, visita a, motivo, horas atrás que entró, minutos que se quedó o None si sigue dentro)
        visitas = [
            ('Carlos', 'Díaz Molina', '79451230', r['1020304001'], 'Visita familiar', 2, None),
            ('Rappi', 'Domicilio', '1032456789', r['1020304005'], 'Entrega de pedido', 0.3, None),
            ('Martha', 'Lucía Pérez', '51876345', r['1020304007'], 'Aseo del apartamento', 4, None),
            ('Jorge', 'Ríos Castaño', '80123456', r['1020304002'], 'Mantenimiento de calentador', 6, 90),
            ('Sofía', 'Navarro León', '1019876543', r['1020304003'], 'Visita de amigos', 26, 180),
            ('Hernán', 'Acosta Ruiz', '79654321', r['1020304009'], 'Técnico de internet', 30, 60),
            ('Gloria', 'Patiño Vera', '41234567', r['1020304010'], 'Visita familiar', 50, 240),
            ('Servientrega', 'Mensajería', '900123456', r['1020304006'], 'Entrega de paquete', 51, 10),
        ]
        for i, (nombre, apellidos, documento, residente, motivo, horas, minutos) in enumerate(visitas):
            ingreso = ahora - timedelta(hours=horas)
            Visitantes.objects.create(
                nombre=nombre, apellidos=apellidos, tipo_documento='CC', num_documento=documento,
                id_residente_fk=residente, motivo=motivo, fecha_ingreso=ingreso,
                fecha_salida=ingreso + timedelta(minutes=minutos) if minutos else None,
                estado='Salió' if minutos else 'Dentro', autorizado_por=guardias[i % len(guardias)],
            )

    def _crear_reservas(self, zonas, residentes):
        hoy = timezone.localdate()
        tz = timezone.get_current_timezone()

        def momento(dias, hora):
            return timezone.make_aware(datetime.combine(hoy + timedelta(days=dias), time(hora)), tz)

        r = residentes
        # (zona, residente, días desde hoy, hora inicio, horas, estado, observaciones)
        datos = [
            ('Salón social', r['1020304001'], 3, 15, 6, 'Aprobada', 'Cumpleaños de mi hija, 35 invitados'),
            ('Zona BBQ', r['1020304002'], 5, 12, 4, 'Pendiente', 'Asado familiar'),
            ('Piscina', r['1020304005'], 2, 10, 3, 'Aprobada', ''),
            ('Cancha múltiple', r['1020304006'], 1, 18, 2, 'Pendiente', 'Partido de microfútbol con vecinos'),
            ('Salón social', r['1020304007'], 10, 18, 5, 'Pendiente', 'Reunión de trabajo'),
            ('Salón de juegos', r['1020304009'], 4, 16, 3, 'Aprobada', ''),
            ('Zona BBQ', r['1020304010'], 7, 13, 4, 'Rechazada', 'Fecha ocupada por mantenimiento'),
            ('Gimnasio', r['1020304003'], 6, 7, 1, 'Cancelada', ''),
            ('Salón social', r['1020304003'], -12, 17, 5, 'Aprobada', 'Primera comunión'),
            ('Zona BBQ', r['1020304001'], -20, 12, 4, 'Aprobada', 'Asado de fin de mes'),
        ]
        reservas = []
        for zona, residente, dias, hora, horas, estado, observaciones in datos:
            inicio = momento(dias, hora)
            reservas.append(Reservas.objects.create(
                id_zona_fk=zonas[zona], id_unidad_fk=residente.id_unidad_fk,
                fecha_reserva=inicio - timedelta(days=7), fecha_inicio=inicio,
                fecha_fin=inicio + timedelta(hours=horas), estado=estado, observaciones=observaciones,
            ))
        return reservas

    def _crear_pagos(self, residentes, reservas):
        hoy = timezone.localdate()
        tz = timezone.get_current_timezone()
        este_mes = hoy.replace(day=1)
        mes_pasado = (este_mes - timedelta(days=1)).replace(day=1)

        def mes(fecha):
            return timezone.make_aware(datetime.combine(fecha, time(0)), tz)

        for i, residente in enumerate(residentes.values()):
            cuota = _cuota(residente.id_unidad_fk)
            # Mes pasado: casi todos pagaron (uno quedó debiendo)
            pagado = i != 3
            Pago.objects.create(
                id_residente_fk=residente, tipo_pago='Administración', mes_ano=mes(mes_pasado), valor=cuota,
                fecha_vencimiento=mes_pasado.replace(day=10),
                estado='Pagado' if pagado else 'Pendiente',
                fecha_pago=mes_pasado.replace(day=min(5 + i % 5, 28)) if pagado else None,
                metodo_pago=f'Tarjeta •••• {4242 + i * 7 % 1000:04d}' if pagado else None,
            )
            # Este mes: algunos ya pagaron, otros están pendientes
            pagado = i % 3 == 0
            Pago.objects.create(
                id_residente_fk=residente, tipo_pago='Administración', mes_ano=mes(este_mes), valor=cuota,
                fecha_vencimiento=este_mes.replace(day=10) if este_mes.replace(day=10) >= hoy else hoy + timedelta(days=10),
                estado='Pagado' if pagado else 'Pendiente',
                fecha_pago=hoy - timedelta(days=1) if pagado else None,
                metodo_pago='Tarjeta •••• 1111' if pagado else None,
            )

        # Parqueadero para quienes tienen carro registrado
        for documento in {v[0] for v in VEHICULOS if v[2] == 'Carro'}:
            Pago.objects.create(id_residente_fk=residentes[documento], tipo_pago='Parqueadero', mes_ano=mes(este_mes),
                                valor=Decimal('85000'), fecha_vencimiento=hoy + timedelta(days=12))

        # Cobro de la reserva aprobada del salón social y una multa por ruido
        salon = reservas[0]
        dueno = Residentes.objects.filter(id_unidad_fk=salon.id_unidad_fk).first()
        Pago.objects.create(id_residente_fk=dueno, tipo_pago='Reserva', id_reserva_fk=salon, mes_ano=mes(este_mes),
                            valor=Decimal('120000'), fecha_vencimiento=hoy + timedelta(days=2))
        Pago.objects.create(id_residente_fk=residentes['1020304008'], tipo_pago='Multa', mes_ano=mes(este_mes),
                            valor=Decimal('150000'), fecha_vencimiento=hoy + timedelta(days=15))

    def _crear_reportes(self, residentes):
        ahora = timezone.now()
        r = residentes
        datos = [
            (r['1020304001'], 'Plomería', 'Gotera en el techo del baño principal desde ayer en la noche.', 'Abierto', 1),
            (r['1020304006'], 'Ascensor', 'El ascensor de la torre B hace un ruido fuerte al frenar en el piso 3.', 'Abierto', 2),
            (r['1020304002'], 'Eléctrico', 'La luz del pasillo del piso 2 está intermitente.', 'En proceso', 4),
            (r['1020304009'], 'Seguridad', 'El citófono del apartamento no timbra cuando llaman de portería.', 'En proceso', 6),
            (r['1020304005'], 'Zonas comunes', 'Una de las sillas plegables del salón social está rota.', 'Cerrado', 15),
            (r['1020304003'], 'Estructural', 'Apareció humedad en la pared de la habitación que da al patio.', 'Abierto', 3),
            (r['1020304010'], 'Plomería', 'La llave del lavaplatos gotea constantemente.', 'Cerrado', 25),
            (r['1020304007'], 'Otro', 'La puerta del shut de basuras de la torre B no cierra bien.', 'En proceso', 8),
        ]
        for residente, categoria, descripcion, estado, dias in datos:
            reporte = ReporteDano.objects.create(
                id_residente_fk=residente, categoria=categoria, descripcion=descripcion,
                torre=residente.id_unidad_fk.torre, piso=residente.id_unidad_fk.piso, estado=estado,
                fecha_resolucion=ahora - timedelta(days=dias - 3) if estado == 'Cerrado' else None,
            )
            # fecha_reporte es auto_now_add: se ajusta después para que los reportes tengan antigüedad real
            ReporteDano.objects.filter(pk=reporte.pk).update(fecha_reporte=ahora - timedelta(days=dias, hours=dias))

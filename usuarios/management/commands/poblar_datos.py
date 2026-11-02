"""Llena la base con datos de ejemplo que tienen sentido entre sí:
torres y apartamentos, zonas comunes, residentes con su cuenta, personal de seguridad,
vehículos, visitas, vehículos de visitantes, paquetes, reservas, facturas y reportes de daños.

    python manage.py poblar_datos

Es seguro ejecutarlo varias veces: si los datos de ejemplo ya existen, no los duplica.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from reservas.datos_iniciales import configurar_zonas
from reservas.models import ItemInventario, ZonasComunes
from residentes.models import Residentes, Unidades
from usuarios import datos_recientes
from usuarios.models import Usuario
from vehiculos.models import Vehiculos

CLAVE_RESIDENTES = 'Conjunto2026'
CLAVE_SEGURIDAD = 'Porteria2026'
CLAVE_JUAN = '123456789'

# Residente (ya existente en la base publicada) al que se le cargan paquetes y reservas de prueba.
# Solo se crean si ese usuario existe y aún no los tiene; nunca se duplican.
USUARIO_PAQUETES_PRUEBA = datos_recientes.USUARIO_PRUEBA

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


class Command(BaseCommand):
    help = 'Carga datos de ejemplo relacionados (torres, zonas, residentes, vigilantes, pagos, etc.).'

    def handle(self, *args, **options):
        juan = self._asegurar_juan_garcia()
        if datos_recientes.paquetes_de_prueba(USUARIO_PAQUETES_PRUEBA):
            self.stdout.write(self.style.SUCCESS(f'Paquetes de prueba cargados para "{USUARIO_PAQUETES_PRUEBA}".'))
        if datos_recientes.reservas_de_prueba(USUARIO_PAQUETES_PRUEBA):
            self.stdout.write(self.style.SUCCESS(f'Reservas de prueba cargadas para "{USUARIO_PAQUETES_PRUEBA}".'))

        if Usuario.objects.filter(username='laura.gomez').exists():
            self.stdout.write('Los datos de ejemplo ya estaban cargados; no se duplicó nada.')
            return

        with transaction.atomic():
            unidades = self._crear_unidades()
            zonas = self._crear_zonas()
            residentes = self._crear_residentes(unidades)
            guardias = self._crear_guardias()
            self._crear_vehiculos(residentes)
            # Visitas, paquetes, reservas, pagos, reportes... con fechas de hoy
            datos_recientes.generar()

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
        configurar_zonas(ZonasComunes, ItemInventario)  # precios, limpieza e inventario
        for zona in zonas.values():
            zona.refresh_from_db()
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

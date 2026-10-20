"""Pruebas de punta a punta: cada rol, cada pantalla y las reglas de negocio principales.

Ejecutar con:  python manage.py test
"""
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from pagos.models import Pago
from reportes.models import ReporteDano
from reservas.models import Reservas, ZonasComunes
from residentes.models import Residentes, Unidades
from usuarios.models import Usuario
from vehiculos.models import Vehiculos
from visitantes.models import Visitantes

CLAVE = 'Clave-Segura-2026'


class BaseConjunto(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user('admin1', 'admin@conjunto.co', CLAVE, rol='admin')
        cls.vigilante = Usuario.objects.create_user('vigilante', 'porteria@conjunto.co', CLAVE, rol='seguridad')
        cls.usuario_res = Usuario.objects.create_user('laura', 'laura@correo.co', CLAVE, rol='residente')
        cls.otro_usuario = Usuario.objects.create_user('pedro', 'pedro@correo.co', CLAVE, rol='residente')

        cls.unidad = Unidades.objects.create(torre='A', apto='101', piso=1, estado=1)
        cls.unidad2 = Unidades.objects.create(torre='B', apto='202', piso=2, estado=1)
        cls.residente = Residentes.objects.create(nombres='Laura', apellidos='Gómez', tipo_documento='CC',
                                                  num_documento='1020', email='laura@correo.co',
                                                  id_unidad_fk=cls.unidad, usuario=cls.usuario_res)
        cls.otro = Residentes.objects.create(nombres='Pedro', apellidos='Ruiz', tipo_documento='CC',
                                             num_documento='3040', email='pedro@correo.co',
                                             id_unidad_fk=cls.unidad2, usuario=cls.otro_usuario)
        cls.zona = ZonasComunes.objects.create(nombre='Salón social', capacidad=40, estado=1)

    def entrar(self, usuario):
        self.client.force_login(usuario)


class PantallasTests(BaseConjunto):
    """Cada pantalla carga (200) para el rol que la usa y queda prohibida (403) para los demás."""

    def test_pantallas_por_rol(self):
        pantallas = {
            self.admin: ['dashboard', 'lista_residentes', 'crear_residente', 'lista_unidades', 'crear_unidad',
                         'lista_vehiculos', 'crear_vehiculo', 'lista_visitantes', 'crear_visitante', 'lista_zonas',
                         'crear_zona', 'lista_reservas', 'crear_reserva', 'lista_pagos_admin', 'crear_pago',
                         'lista_reportes_admin', 'cambiar_password', 'lista_guardias', 'crear_guardia'],
            self.usuario_res: ['dashboard', 'lista_vehiculos', 'crear_vehiculo', 'lista_zonas', 'lista_reservas',
                               'crear_reserva', 'lista_pagos_residente', 'mis_reportes', 'crear_reporte'],
            self.vigilante: ['dashboard', 'lista_visitantes', 'crear_visitante', 'lista_vehiculos'],
        }
        for usuario, rutas in pantallas.items():
            self.entrar(usuario)
            for ruta in rutas:
                with self.subTest(usuario=usuario.username, ruta=ruta):
                    self.assertEqual(self.client.get(reverse(ruta)).status_code, 200)

    def test_prohibido_para_otros_roles(self):
        self.entrar(self.usuario_res)
        for ruta in ['lista_residentes', 'lista_pagos_admin', 'lista_visitantes', 'crear_pago', 'crear_zona',
                     'lista_guardias', 'crear_guardia']:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 403)
        self.entrar(self.vigilante)
        self.assertEqual(self.client.get(reverse('crear_vehiculo')).status_code, 403)

    def test_registro_viejo_sin_nombre_no_rompe_las_listas(self):
        Residentes.objects.create()  # como el que vino del volcado de MySQL
        self.entrar(self.admin)
        for ruta in ['lista_residentes', 'crear_pago', 'crear_visitante', 'crear_vehiculo']:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 200)

    def test_inicio_redirige(self):
        self.assertRedirects(self.client.get('/'), reverse('login'), target_status_code=200)
        self.entrar(self.admin)
        self.assertRedirects(self.client.get('/'), reverse('dashboard'))

    def test_sin_sesion_va_al_login(self):
        respuesta = self.client.get(reverse('lista_residentes'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta['Location'])


class SesionTests(BaseConjunto):
    def test_login_y_logout(self):
        respuesta = self.client.post(reverse('login'), {'username': 'laura', 'password': CLAVE})
        self.assertRedirects(respuesta, reverse('dashboard'))
        # El logout funciona con POST (Django 5+ no acepta GET)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('login'), target_status_code=200)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)

    def test_login_incorrecto_muestra_error(self):
        respuesta = self.client.post(reverse('login'), {'username': 'laura', 'password': 'mala'})
        self.assertContains(respuesta, 'Usuario o contraseña incorrectos')

    def test_login_sin_distinguir_mayusculas(self):
        respuesta = self.client.post(reverse('login'), {'username': 'LAURA', 'password': CLAVE})
        self.assertRedirects(respuesta, reverse('dashboard'))

    def test_contrasena_asignada_por_admin_obliga_a_cambiarla(self):
        self.entrar(self.admin)
        respuesta = self.client.post(reverse('asignar_password', args=[self.usuario_res.pk]), {
            'new_password1': 'Puesta-Por-Admin-1', 'new_password2': 'Puesta-Por-Admin-1', 'exigir_cambio': 'on'})
        self.assertRedirects(respuesta, reverse('lista_residentes'))
        self.usuario_res.refresh_from_db()
        self.assertTrue(self.usuario_res.check_password('Puesta-Por-Admin-1'))

        self.entrar(self.usuario_res)
        self.assertRedirects(self.client.get(reverse('lista_pagos_residente')), reverse('cambiar_password'))

        respuesta = self.client.post(reverse('cambiar_password'), {
            'old_password': 'Puesta-Por-Admin-1', 'new_password1': 'Nueva-Clave-789', 'new_password2': 'Nueva-Clave-789'})
        self.assertRedirects(respuesta, reverse('password_change_done'))
        self.usuario_res.refresh_from_db()
        self.assertFalse(self.usuario_res.debe_cambiar_password)
        self.assertEqual(self.client.get(reverse('lista_pagos_residente')).status_code, 200)


class ResidentesTests(BaseConjunto):
    def test_crear_residente_no_genera_cuenta_ni_contrasena(self):
        self.entrar(self.admin)
        usuarios_antes = Usuario.objects.count()
        respuesta = self.client.post(reverse('crear_residente'), {
            'nombres': 'Ana', 'apellidos': 'Torres', 'tipo_documento': 'CC', 'num_documento': '5566',
            'telefono': '3001112233', 'email': 'Ana.Torres@Correo.co', 'id_unidad_fk': self.unidad2.pk,
        }, follow=True)
        residente = Residentes.objects.get(num_documento='5566')
        self.assertEqual(residente.email, 'ana.torres@correo.co')
        self.assertIsNotNone(residente.fecha_registro)
        self.assertIsNone(residente.usuario)
        self.assertEqual(Usuario.objects.count(), usuarios_antes)
        self.assertContains(respuesta, 'Registrarse')

    def test_documento_repetido(self):
        self.entrar(self.admin)
        respuesta = self.client.post(reverse('crear_residente'), {
            'nombres': 'Otra', 'apellidos': 'Laura', 'tipo_documento': 'CC', 'num_documento': '1020'})
        self.assertContains(respuesta, 'Ya existe un residente con este número de documento')

    def test_editar_correo_sincroniza_la_cuenta(self):
        self.entrar(self.admin)
        self.client.post(reverse('editar_residente', args=[self.residente.pk]), {
            'nombres': 'Laura', 'apellidos': 'Gómez', 'tipo_documento': 'CC', 'num_documento': '1020',
            'email': 'laura.nueva@correo.co', 'id_unidad_fk': self.unidad.pk})
        self.usuario_res.refresh_from_db()
        self.assertEqual(self.usuario_res.email, 'laura.nueva@correo.co')

    def test_busqueda_por_documento(self):
        self.entrar(self.admin)
        respuesta = self.client.get(reverse('lista_residentes'), {'buscar': '3040'})
        self.assertEqual(list(respuesta.context['residentes']), [self.otro])

    def test_unidad_repetida_y_eliminar_con_residentes(self):
        self.entrar(self.admin)
        respuesta = self.client.post(reverse('crear_unidad'), {'torre': 'a', 'apto': '101', 'piso': 1, 'estado': 1})
        self.assertContains(respuesta, 'ya existe')
        self.client.post(reverse('eliminar_unidad', args=[self.unidad.pk]))
        self.assertTrue(Unidades.objects.filter(pk=self.unidad.pk).exists())


class VehiculosTests(BaseConjunto):
    def test_placa_en_mayusculas_y_propietario_forzado(self):
        self.entrar(self.usuario_res)
        self.client.post(reverse('crear_vehiculo'), {
            'tipo_vehiculo': 'Carro', 'placa': 'abc 123', 'marca': 'Mazda', 'modelo': '3', 'color': 'Rojo',
            'estado': 'Activo', 'id_residente_fk': self.otro.pk})
        vehiculo = Vehiculos.objects.get()
        self.assertEqual(vehiculo.placa, 'ABC123')
        self.assertEqual(vehiculo.id_residente_fk, self.residente)

    def test_placa_repetida(self):
        Vehiculos.objects.create(placa='XYZ789', tipo_vehiculo='Carro', id_residente_fk=self.otro)
        self.entrar(self.admin)
        respuesta = self.client.post(reverse('crear_vehiculo'), {
            'tipo_vehiculo': 'Carro', 'placa': 'xyz789', 'marca': 'Kia', 'color': 'Gris',
            'estado': 'Activo', 'id_residente_fk': self.residente.pk})
        self.assertContains(respuesta, 'Ya hay un vehículo registrado con esta placa')

    def test_residente_no_edita_vehiculo_ajeno(self):
        ajeno = Vehiculos.objects.create(placa='QWE456', tipo_vehiculo='Carro', id_residente_fk=self.otro)
        self.entrar(self.usuario_res)
        self.assertEqual(self.client.get(reverse('editar_vehiculo', args=[ajeno.pk])).status_code, 404)
        self.client.post(reverse('eliminar_vehiculo', args=[ajeno.pk]))
        self.assertTrue(Vehiculos.objects.filter(pk=ajeno.pk).exists())


class ReservasTests(BaseConjunto):
    def datos(self, horas_desde_ahora=24, duracion=3):
        inicio = timezone.localtime() + timedelta(hours=horas_desde_ahora)
        fin = inicio + timedelta(hours=duracion)
        return {'id_zona_fk': self.zona.pk, 'fecha_inicio': inicio.strftime('%Y-%m-%dT%H:%M'),
                'fecha_fin': fin.strftime('%Y-%m-%dT%H:%M'), 'observaciones': 'Cumpleaños'}

    def test_residente_reserva_queda_pendiente_en_su_unidad(self):
        self.entrar(self.usuario_res)
        datos = self.datos()
        datos.update({'estado': 'Aprobada', 'id_unidad_fk': self.unidad2.pk})  # intenta saltarse las reglas
        self.client.post(reverse('crear_reserva'), datos)
        reserva = Reservas.objects.get()
        self.assertEqual(reserva.estado, 'Pendiente')
        self.assertEqual(reserva.id_unidad_fk, self.unidad)
        self.assertIsNotNone(reserva.fecha_reserva)

    def test_choque_de_horario_y_cancelada_libera(self):
        self.entrar(self.usuario_res)
        self.client.post(reverse('crear_reserva'), self.datos())
        respuesta = self.client.post(reverse('crear_reserva'), self.datos(horas_desde_ahora=25))
        self.assertContains(respuesta, 'ya está reservada')
        reserva = Reservas.objects.get()
        self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]), {'estado': 'Cancelada'})
        self.client.post(reverse('crear_reserva'), self.datos(horas_desde_ahora=25))
        self.assertEqual(Reservas.objects.count(), 2)

    def test_admin_aprueba_y_residente_no_puede_aprobar(self):
        self.entrar(self.usuario_res)
        self.client.post(reverse('crear_reserva'), self.datos())
        reserva = Reservas.objects.get()
        self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]), {'estado': 'Aprobada'})
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'Pendiente')
        self.entrar(self.admin)
        self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]), {'estado': 'Aprobada'})
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'Aprobada')

    def test_fecha_pasada_rechazada(self):
        self.entrar(self.usuario_res)
        respuesta = self.client.post(reverse('crear_reserva'), self.datos(horas_desde_ahora=-5))
        self.assertContains(respuesta, 'no puede estar en el pasado')

    def test_residente_sin_unidad_recibe_aviso(self):
        self.otro.id_unidad_fk = None
        self.otro.save()
        self.entrar(self.otro_usuario)
        respuesta = self.client.get(reverse('crear_reserva'), follow=True)
        self.assertContains(respuesta, 'necesitas tener una unidad asignada')

    def test_next_externo_no_redirige_fuera(self):
        self.entrar(self.admin)
        reserva = Reservas.objects.create(id_zona_fk=self.zona, id_unidad_fk=self.unidad, estado='Pendiente',
                                          fecha_inicio=timezone.now() + timedelta(days=1),
                                          fecha_fin=timezone.now() + timedelta(days=1, hours=2))
        respuesta = self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]),
                                     {'estado': 'Aprobada', 'next': 'https://sitio-malicioso.com/'})
        self.assertEqual(respuesta['Location'], reverse('lista_reservas'))


class PagosTests(BaseConjunto):
    def crear_factura(self, dias_para_vencer=10):
        return Pago.objects.create(id_residente_fk=self.residente, tipo_pago='Administración',
                                   mes_ano=timezone.now(), valor=320000,
                                   fecha_vencimiento=timezone.localdate() + timedelta(days=dias_para_vencer))

    def test_admin_genera_factura(self):
        self.entrar(self.admin)
        self.client.post(reverse('crear_pago'), {
            'id_residente_fk': self.residente.pk, 'tipo_pago': 'Administración', 'mes_ano': '2026-10',
            'valor': '320000', 'fecha_vencimiento': (timezone.localdate() + timedelta(days=15)).isoformat()})
        pago = Pago.objects.get()
        self.assertEqual(pago.estado, 'Pendiente')
        self.assertEqual(pago.mes_ano.day, 1)

    def test_pago_simulado(self):
        pago = self.crear_factura()
        self.entrar(self.usuario_res)
        self.client.post(reverse('pasarela_pago', args=[pago.pk]), {
            'nombre_titular': 'Laura Gómez', 'numero_tarjeta': '4111 1111 1111 1111',
            'fecha_expiracion': '12/30', 'cvv': '123'})
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'Pagado')
        self.assertEqual(pago.metodo_pago, 'Tarjeta •••• 1111')

    def test_tarjeta_vencida_y_numero_invalido(self):
        pago = self.crear_factura()
        self.entrar(self.usuario_res)
        respuesta = self.client.post(reverse('pasarela_pago', args=[pago.pk]), {
            'nombre_titular': 'Laura', 'numero_tarjeta': '4111 1111 1111 1112', 'fecha_expiracion': '01/20', 'cvv': '123'})
        self.assertContains(respuesta, 'La tarjeta está vencida')
        self.assertContains(respuesta, 'no es válido')

    def test_residente_no_paga_factura_ajena(self):
        pago = Pago.objects.create(id_residente_fk=self.otro, tipo_pago='Multa', mes_ano=timezone.now(),
                                   valor=50000, fecha_vencimiento=timezone.localdate())
        self.entrar(self.usuario_res)
        self.assertEqual(self.client.get(reverse('pasarela_pago', args=[pago.pk])).status_code, 404)

    def test_filtro_vencidos_y_anular(self):
        vencido = self.crear_factura(dias_para_vencer=-3)
        self.crear_factura()
        self.entrar(self.admin)
        respuesta = self.client.get(reverse('lista_pagos_admin'), {'estado': 'vencido'})
        self.assertEqual(list(respuesta.context['pagos']), [vencido])
        self.client.post(reverse('anular_pago', args=[vencido.pk]))
        self.assertFalse(Pago.objects.filter(pk=vencido.pk).exists())


class VisitantesYReportesTests(BaseConjunto):
    def test_registro_de_visitante_y_salida(self):
        self.entrar(self.vigilante)
        self.client.post(reverse('crear_visitante'), {
            'nombre': 'Carlos', 'apellidos': 'Díaz', 'tipo_documento': 'CC', 'num_documento': '111',
            'id_residente_fk': self.residente.pk, 'motivo': 'Visita familiar, 2 personas.',
            'fecha_ingreso': timezone.localtime().strftime('%Y-%m-%dT%H:%M'), 'estado': 'Dentro'})
        visitante = Visitantes.objects.get()
        self.assertEqual(visitante.autorizado_por, self.vigilante)
        self.client.post(reverse('registrar_salida', args=[visitante.pk]))
        visitante.refresh_from_db()
        self.assertEqual(visitante.estado, 'Salió')
        self.assertIsNotNone(visitante.fecha_salida)

    def test_reporte_y_cambio_de_estado(self):
        self.entrar(self.usuario_res)
        self.assertEqual(self.client.get(reverse('crear_reporte')).context['form'].initial.get('torre'), 'A')
        self.client.post(reverse('crear_reporte'), {
            'categoria': 'Plomería', 'torre': 'a', 'piso': 1, 'descripcion': 'Gotera en el techo del baño.'})
        reporte = ReporteDano.objects.get()
        self.assertEqual((reporte.estado, reporte.torre), ('Abierto', 'A'))

        self.entrar(self.admin)
        self.client.post(reverse('cambiar_estado_reporte', args=[reporte.pk]), {'estado': 'Cerrado'})
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, 'Cerrado')
        self.assertIsNotNone(reporte.fecha_resolucion)


class RegistroTests(BaseConjunto):
    """El residente crea su cuenta eligiendo usuario y contraseña."""

    def setUp(self):
        self.sin_cuenta = Residentes.objects.create(nombres='Paula', apellidos='Mendoza', tipo_documento='CC',
                                                    num_documento='5050', email='paula@correo.co',
                                                    id_unidad_fk=self.unidad2)

    def datos(self, **cambios):
        datos = {'tipo_documento': 'CC', 'num_documento': '5050', 'email': 'Paula@Correo.co',
                 'username': 'paula.m', 'password1': 'MiClave-Segura-55', 'password2': 'MiClave-Segura-55'}
        datos.update(cambios)
        return datos

    def test_registro_exitoso_y_entra_al_panel(self):
        respuesta = self.client.post(reverse('registro'), self.datos())
        self.assertRedirects(respuesta, reverse('dashboard'))
        self.sin_cuenta.refresh_from_db()
        usuario = self.sin_cuenta.usuario
        self.assertEqual((usuario.username, usuario.rol), ('paula.m', 'residente'))
        self.assertFalse(usuario.debe_cambiar_password)
        self.client.logout()
        self.assertTrue(self.client.login(username='paula.m', password='MiClave-Segura-55'))

    def test_documento_desconocido(self):
        respuesta = self.client.post(reverse('registro'), self.datos(num_documento='9999'))
        self.assertContains(respuesta, 'No encontramos un residente con ese documento')

    def test_correo_distinto_al_registrado(self):
        respuesta = self.client.post(reverse('registro'), self.datos(email='otra@correo.co'))
        self.assertContains(respuesta, 'El correo no coincide')

    def test_residente_que_ya_tiene_cuenta(self):
        respuesta = self.client.post(reverse('registro'), self.datos(num_documento='1020', email='laura@correo.co'))
        self.assertContains(respuesta, 'ya tiene una cuenta')

    def test_usuario_repetido_sin_importar_mayusculas(self):
        respuesta = self.client.post(reverse('registro'), self.datos(username='LAURA'))
        self.assertContains(respuesta, 'ya está en uso')

    def test_contrasena_debil_rechazada(self):
        respuesta = self.client.post(reverse('registro'), self.datos(password1='123456789', password2='123456789'))
        self.assertEqual(respuesta.status_code, 200)
        self.sin_cuenta.refresh_from_db()
        self.assertIsNone(self.sin_cuenta.usuario)

    def test_login_y_registro_se_enlazan(self):
        self.assertContains(self.client.get(reverse('login')), reverse('registro'))
        self.assertContains(self.client.get(reverse('registro')), reverse('login'))


class GuardiasTests(BaseConjunto):
    def test_admin_crea_vigilante_con_sus_credenciales(self):
        self.entrar(self.admin)
        self.client.post(reverse('crear_guardia'), {
            'first_name': 'Oscar', 'last_name': 'Pena', 'username': 'oscar.pena', 'email': 'oscar@conjunto.co',
            'is_active': 'on', 'password1': 'Porteria-Norte-7', 'password2': 'Porteria-Norte-7'})
        guardia = Usuario.objects.get(username='oscar.pena')
        self.assertEqual(guardia.rol, 'seguridad')
        self.client.logout()
        self.assertTrue(self.client.login(username='oscar.pena', password='Porteria-Norte-7'))
        self.assertEqual(self.client.get(reverse('crear_visitante')).status_code, 200)

    def test_contrasenas_distintas(self):
        self.entrar(self.admin)
        respuesta = self.client.post(reverse('crear_guardia'), {
            'first_name': 'Ana', 'last_name': 'Ruiz', 'username': 'ana.ruiz', 'is_active': 'on',
            'password1': 'Porteria-Norte-7', 'password2': 'Otra-Clave-99'})
        self.assertContains(respuesta, 'no coinciden')

    def test_eliminar_con_visitas_solo_desactiva(self):
        Visitantes.objects.create(nombre='Carlos', apellidos='Diaz', id_residente_fk=self.residente,
                                  fecha_ingreso=timezone.now(), estado='Dentro', autorizado_por=self.vigilante)
        self.entrar(self.admin)
        self.client.post(reverse('eliminar_guardia', args=[self.vigilante.pk]))
        self.vigilante.refresh_from_db()
        self.assertFalse(self.vigilante.is_active)

    def test_eliminar_sin_visitas_borra(self):
        nuevo = Usuario.objects.create_user('temporal', password=CLAVE, rol='seguridad')
        self.entrar(self.admin)
        self.client.post(reverse('eliminar_guardia', args=[nuevo.pk]))
        self.assertFalse(Usuario.objects.filter(pk=nuevo.pk).exists())

    def test_no_se_puede_tocar_un_admin_desde_seguridad(self):
        self.entrar(self.admin)
        self.assertEqual(self.client.get(reverse('editar_guardia', args=[self.admin.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('asignar_password', args=[self.admin.pk])).status_code, 404)


class IdiomaTests(BaseConjunto):
    def test_cambiar_a_ingles_y_volver(self):
        self.entrar(self.admin)
        self.client.post(reverse('set_language'), {'language': 'en', 'next': reverse('dashboard')})
        respuesta = self.client.get(reverse('dashboard'))
        self.assertContains(respuesta, 'Admin dashboard')
        self.assertContains(respuesta, 'Sign out')
        self.assertContains(respuesta, '<html lang="en">')
        self.client.post(reverse('set_language'), {'language': 'es', 'next': reverse('dashboard')})
        self.assertContains(self.client.get(reverse('dashboard')), 'Cerrar sesión')

    def test_login_en_ingles(self):
        self.client.post(reverse('set_language'), {'language': 'en', 'next': '/'})
        respuesta = self.client.get(reverse('login'))
        self.assertContains(respuesta, 'Sign in')
        self.assertContains(respuesta, 'Are you a resident without an account?')


class PoblarDatosTests(TestCase):
    def test_carga_datos_relacionados_y_juan_garcia(self):
        call_command('poblar_datos', verbosity=0)
        self.assertEqual(Unidades.objects.count(), 30)
        self.assertEqual(ZonasComunes.objects.count(), 7)
        self.assertEqual(Usuario.objects.filter(rol='seguridad').count(), 3)
        self.assertTrue(Residentes.objects.filter(usuario__isnull=True).exists())  # algunos aún deben registrarse
        for vehiculo in Vehiculos.objects.all():
            self.assertIsNotNone(vehiculo.id_residente_fk.usuario_id)
        self.assertTrue(self.client.login(username='Juan_Garcia', password='123456789'))
        self.assertTrue(self.client.login(username='juan_garcia', password='123456789'))
        self.assertTrue(self.client.login(username='laura.gomez', password='Conjunto2026'))
        self.assertTrue(self.client.login(username='carlos.mejia', password='Porteria2026'))

    def test_no_duplica_al_repetirse(self):
        call_command('poblar_datos', verbosity=0)
        totales = (Residentes.objects.count(), Pago.objects.count(), Reservas.objects.count())
        call_command('poblar_datos', verbosity=0)
        self.assertEqual(totales, (Residentes.objects.count(), Pago.objects.count(), Reservas.objects.count()))

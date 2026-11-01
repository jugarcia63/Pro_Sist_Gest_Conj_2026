from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from pagos.models import Pago
from parqueadero.models import ParqueoVisitante
from reservas.models import ItemInventario, Reservas, ZonasComunes
from reservas.tests import momento
from residentes.models import Residentes
from usuarios.models import Usuario
from usuarios.tests import BaseConjunto
from .models import Aviso


class AvisosTests(BaseConjunto):

    def test_paquete_avisa_a_toda_la_unidad(self):
        companera = Usuario.objects.create_user('sofia', 'sofia@correo.co', 'Clave-Segura-2026', rol='residente')
        Residentes.objects.create(nombres='Sofía', apellidos='Gómez', num_documento='5566', id_unidad_fk=self.unidad,
                                  usuario=companera)
        self.entrar(self.vigilante)
        self.client.post(reverse('crear_paquete'), {'numero_guia': 'G1', 'empresa': 'TCC', 'destinatario': 'Laura',
                                                    'id_unidad_fk': self.unidad.pk})
        self.assertEqual(set(Aviso.objects.filter(tipo='paquete').values_list('usuario__username', flat=True)),
                         {'laura', 'sofia'})
        self.assertFalse(Aviso.objects.filter(usuario=self.otro_usuario).exists())

    def test_campana_lista_y_marcar_leidos(self):
        Aviso.objects.create(usuario=self.usuario_res, tipo='paquete', titulo='Llegó un paquete a portería',
                             url=reverse('mis_paquetes'))
        self.entrar(self.usuario_res)
        self.assertContains(self.client.get(reverse('dashboard')), 'topbar__avisos-cuenta')
        pagina = self.client.get(reverse('lista_avisos'))
        self.assertContains(pagina, 'Llegó un paquete a portería')
        self.assertContains(pagina, 'aviso-item--nuevo')  # se ve resaltado la primera vez
        self.assertFalse(Aviso.objects.filter(leido=False).exists())
        self.assertNotContains(self.client.get(reverse('dashboard')), 'topbar__avisos-cuenta')
        aviso = Aviso.objects.get()
        self.assertRedirects(self.client.get(reverse('abrir_aviso', args=[aviso.pk])), reverse('mis_paquetes'))
        # Nadie abre avisos ajenos
        self.entrar(self.otro_usuario)
        self.assertEqual(self.client.get(reverse('abrir_aviso', args=[aviso.pk])).status_code, 404)

    def test_reserva_aprobada_y_rechazada(self):
        zona = ZonasComunes.objects.create(nombre='Salón', estado=1, valor_hora=Decimal('25000'))
        reserva = Reservas.objects.create(id_zona_fk=zona, id_unidad_fk=self.unidad, reservado_por=self.usuario_res,
                                          fecha_inicio=momento(3, 15), fecha_fin=momento(3, 18), estado='Pendiente')
        reserva.calcular_cobro()
        reserva.save()
        self.entrar(self.admin)
        self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]), {'estado': 'Aprobada'})
        aviso = Aviso.objects.get(usuario=self.usuario_res)
        self.assertEqual(aviso.titulo, 'Tu reserva fue aprobada')
        self.assertIn('$75.000', aviso.mensaje)
        self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]), {'estado': 'Rechazada'})
        self.assertTrue(Aviso.objects.filter(usuario=self.usuario_res, titulo='Tu reserva fue rechazada').exists())

    def test_multa_por_entrega_y_factura_del_admin(self):
        zona = ZonasComunes.objects.create(nombre='BBQ', estado=1)
        silla = ItemInventario.objects.create(zona=zona, nombre='Sillas', cantidad=4, valor_reposicion=Decimal('45000'))
        reserva = Reservas.objects.create(id_zona_fk=zona, id_unidad_fk=self.unidad, reservado_por=self.usuario_res,
                                          fecha_inicio=timezone.now() - timedelta(hours=3),
                                          fecha_fin=timezone.now() - timedelta(hours=1), estado='Aprobada')
        reserva.calcular_cobro()
        reserva.save()
        self.entrar(self.vigilante)
        self.client.post(reverse('recibir_zona', args=[reserva.pk]),
                         {f'faltan_{silla.pk}': 1, f'danados_{silla.pk}': 0, 'zona_limpia': 'si'})
        self.assertTrue(Aviso.objects.filter(usuario=self.usuario_res, tipo='multa', titulo='Tienes una multa').exists())

        self.entrar(self.admin)
        self.client.post(reverse('crear_pago'), {
            'id_residente_fk': self.otro.pk, 'tipo_pago': 'Administración', 'mes_ano': timezone.localdate().strftime('%Y-%m'),
            'valor': '320000', 'fecha_vencimiento': (timezone.localdate() + timedelta(days=10)).isoformat()})
        self.assertTrue(Aviso.objects.filter(usuario=self.otro_usuario, tipo='factura').exists())


class CorreosTests(BaseConjunto):

    def test_sin_configurar_no_se_envia_nada(self):
        self.entrar(self.vigilante)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('crear_paquete'), {'numero_guia': 'G2', 'destinatario': 'Laura',
                                                        'id_unidad_fk': self.unidad.pk})
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(Aviso.objects.exists())  # el aviso en la app sí se crea

    @override_settings(CORREOS_ACTIVOS=True)
    def test_el_aviso_tambien_llega_por_correo(self):
        self.entrar(self.vigilante)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('crear_paquete'), {'numero_guia': 'G3', 'destinatario': 'Laura',
                                                        'id_unidad_fk': self.unidad.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['laura@correo.co'])
        self.assertIn('Llegó un paquete', mail.outbox[0].subject)

    @override_settings(CORREOS_ACTIVOS=True)
    def test_bienvenida_al_crear_la_cuenta(self):
        nuevo = Residentes.objects.create(nombres='Paula', apellidos='Méndez', num_documento='9090',
                                          email='paula@correo.co', id_unidad_fk=self.unidad2)
        self.entrar(self.admin)
        url = reverse('crear_cuenta_residente', args=[nuevo.pk])
        self.assertContains(self.client.get(url), 'Enviarle por correo')
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, {'username': 'paula.m', 'password1': 'Temporal-Segura-55',
                                   'password2': 'Temporal-Segura-55', 'enviar_correo': 'on'})
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['paula@correo.co'])
        self.assertIn('paula.m', correo.body)
        self.assertIn('Temporal-Segura-55', correo.body)

    def test_sin_correos_no_aparece_la_casilla(self):
        nuevo = Residentes.objects.create(nombres='Paula', apellidos='Méndez', num_documento='9091',
                                          email='paula2@correo.co', id_unidad_fk=self.unidad2)
        self.entrar(self.admin)
        self.assertNotContains(self.client.get(reverse('crear_cuenta_residente', args=[nuevo.pk])), 'Enviarle por correo')


class CalendarioTests(BaseConjunto):

    def test_muestra_ocupados_y_huecos_libres(self):
        zona = ZonasComunes.objects.create(nombre='Salón social', estado=1)
        Reservas.objects.create(id_zona_fk=zona, id_unidad_fk=self.unidad2, fecha_inicio=momento(2, 15),
                                fecha_fin=momento(2, 18), estado='Aprobada')
        Reservas.objects.create(id_zona_fk=zona, id_unidad_fk=self.unidad2, fecha_inicio=momento(2, 8),
                                fecha_fin=momento(2, 10), estado='Cancelada')
        self.entrar(self.usuario_res)
        semana = (timezone.localdate() + timedelta(days=2)).isoformat()
        pagina = self.client.get(reverse('calendario_zona', args=[zona.pk]), {'semana': semana})
        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, '15:00–18:00')
        self.assertContains(pagina, 'Ocupado')
        self.assertNotContains(pagina, '08:00–10:00')  # la cancelada libera el horario
        self.assertNotContains(pagina, 'Torre B')     # el residente no ve de quién es
        dia = (timezone.localdate() + timedelta(days=2)).isoformat()
        self.assertContains(pagina, f'inicio={dia}T10:00')       # hueco libre
        self.assertNotContains(pagina, f'inicio={dia}T16:00')    # ocupado

    def test_hueco_libre_prellena_la_reserva(self):
        zona = ZonasComunes.objects.create(nombre='BBQ', estado=1)
        self.entrar(self.usuario_res)
        inicio = momento(4, 14).strftime('%Y-%m-%dT%H:%M')
        formulario = self.client.get(reverse('crear_reserva'), {'zona': zona.pk, 'inicio': inicio}).context['form']
        self.assertEqual(formulario.initial['fecha_inicio'], inicio)
        self.assertEqual(formulario.initial['fecha_fin'], momento(4, 16).strftime('%Y-%m-%dT%H:%M'))

    def test_seguridad_no_entra(self):
        zona = ZonasComunes.objects.create(nombre='BBQ', estado=1)
        self.entrar(self.vigilante)
        self.assertEqual(self.client.get(reverse('calendario_zona', args=[zona.pk])).status_code, 403)


class RecaudoTests(BaseConjunto):

    def test_totales_por_mes_y_concepto(self):
        anio = timezone.localdate().year
        marzo = timezone.localdate().replace(month=3, day=10)
        base = {'mes_ano': timezone.now(), 'fecha_vencimiento': marzo}
        Pago.objects.create(id_residente_fk=self.residente, tipo_pago='Administración', valor=Decimal('300000'),
                            estado='Pagado', fecha_pago=marzo, **base)
        Pago.objects.create(id_residente_fk=self.residente, tipo_pago='Multa', valor=Decimal('45000'),
                            estado='Pagado', fecha_pago=marzo, **base)
        Pago.objects.create(id_residente_fk=self.residente, tipo_pago='Reserva', valor=Decimal('90000'),
                            estado='Pendiente', **base)  # no cuenta como recaudo
        ParqueoVisitante.objects.create(placa='AAA111', id_unidad_fk=self.unidad, valor_hora=2000, horas_gratis=2,
                                        fecha_ingreso=timezone.now() - timedelta(hours=4),
                                        fecha_salida=timezone.now(), valor_cobrado=Decimal('4000'), estado='Salió')
        self.entrar(self.admin)
        pagina = self.client.get(reverse('reporte_recaudo'), {'anio': anio})
        self.assertEqual(pagina.context['total'], Decimal('349000'))
        marzo_fila = pagina.context['filas'][2]
        self.assertEqual(marzo_fila['total'], Decimal('345000'))
        self.assertEqual(pagina.context['por_cobrar'], Decimal('90000'))

        csv = self.client.get(reverse('reporte_recaudo'), {'anio': anio, 'formato': 'csv'})
        self.assertIn('attachment', csv['Content-Disposition'])
        self.assertIn('345000', csv.content.decode('utf-8-sig'))
        pdf = self.client.get(reverse('reporte_recaudo'), {'anio': anio, 'formato': 'pdf'})
        self.assertTrue(pdf.content.startswith(b'%PDF'))

    def test_solo_admin(self):
        for usuario in (self.usuario_res, self.vigilante):
            self.entrar(usuario)
            self.assertEqual(self.client.get(reverse('reporte_recaudo')).status_code, 403)

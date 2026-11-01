from datetime import datetime, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from pagos.models import Pago
from usuarios.tests import BaseConjunto
from .models import ItemInventario, Reservas, ZonasComunes, horas_a_cobrar


def momento(dias, hora, minuto=0):
    base = timezone.localdate() + timedelta(days=dias)
    return timezone.make_aware(datetime(base.year, base.month, base.day, hora, minuto))


class HorasACobrarTests(BaseConjunto):
    """Sin horas gratis: cada hora iniciada se cobra desde el primer segundo."""

    def test_cada_hora_iniciada_cuenta_completa(self):
        inicio = momento(1, 10)
        casos = {timedelta(seconds=1): 1, timedelta(minutes=59): 1, timedelta(hours=1): 1,
                 timedelta(hours=1, seconds=1): 2, timedelta(hours=4): 4, timedelta(hours=4, minutes=30): 5}
        for duracion, horas in casos.items():
            with self.subTest(duracion=duracion):
                self.assertEqual(horas_a_cobrar(inicio, inicio + duracion), horas)
        self.assertEqual(horas_a_cobrar(inicio, inicio), 0)


class ReservasConCobroTests(BaseConjunto):

    def setUp(self):
        self.bbq = ZonasComunes.objects.create(nombre='Zona BBQ', capacidad=20, estado=1, valor_hora=Decimal('15000'),
                                               ofrece_limpieza=True, valor_limpieza=Decimal('30000'))
        self.parrilla = ItemInventario.objects.create(zona=self.bbq, nombre='Parrilla a gas', cantidad=1,
                                                      valor_reposicion=Decimal('1500000'))
        self.sillas = ItemInventario.objects.create(zona=self.bbq, nombre='Sillas', cantidad=16,
                                                    valor_reposicion=Decimal('45000'))

    def reservar(self, limpieza=False, dias=3, hora=12, horas=4):
        self.entrar(self.usuario_res)
        datos = {'id_zona_fk': self.bbq.pk, 'fecha_inicio': momento(dias, hora).strftime('%Y-%m-%dT%H:%M'),
                 'fecha_fin': momento(dias, hora + horas).strftime('%Y-%m-%dT%H:%M'), 'observaciones': 'Asado'}
        if limpieza:
            datos['incluye_limpieza'] = 'on'
        self.client.post(reverse('crear_reserva'), datos)
        return Reservas.objects.latest('pk')

    def aprobar(self, reserva):
        self.entrar(self.admin)
        self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]), {'estado': 'Aprobada'})
        reserva.refresh_from_db()
        return reserva

    def test_la_reserva_copia_la_tarifa_y_suma_la_limpieza(self):
        reserva = self.reservar(limpieza=True)
        self.assertEqual(reserva.reservado_por, self.usuario_res)
        self.assertEqual((reserva.horas_cobradas, reserva.valor_hora), (4, Decimal('15000')))
        self.assertEqual(reserva.valor_total, Decimal('90000'))  # 4 × 15.000 + 30.000
        # Un cambio de precio después no afecta la reserva ya hecha
        self.bbq.valor_hora = Decimal('99000')
        self.bbq.save()
        reserva.refresh_from_db()
        self.assertEqual(reserva.valor_total, Decimal('90000'))

    def test_la_factura_se_genera_al_aprobar_y_se_anula_al_cancelar(self):
        reserva = self.reservar()
        self.assertFalse(Pago.objects.filter(id_reserva_fk=reserva).exists())  # pendiente: sin factura
        reserva = self.aprobar(reserva)
        factura = Pago.objects.get(id_reserva_fk=reserva)
        self.assertEqual((factura.tipo_pago, factura.valor, factura.estado), ('Reserva', Decimal('60000'), 'Pendiente'))
        self.assertEqual(factura.id_residente_fk, self.residente)

        self.entrar(self.usuario_res)
        self.client.post(reverse('cambiar_estado_reserva', args=[reserva.pk]), {'estado': 'Cancelada'})
        self.assertFalse(Pago.objects.filter(id_reserva_fk=reserva).exists())

    def test_zona_gratuita_no_genera_factura_ni_limpieza(self):
        gratis = ZonasComunes.objects.create(nombre='Cancha', capacidad=14, estado=1)
        self.entrar(self.usuario_res)
        self.client.post(reverse('crear_reserva'), {
            'id_zona_fk': gratis.pk, 'incluye_limpieza': 'on',
            'fecha_inicio': momento(2, 18).strftime('%Y-%m-%dT%H:%M'), 'fecha_fin': momento(2, 20).strftime('%Y-%m-%dT%H:%M')})
        reserva = self.aprobar(Reservas.objects.latest('pk'))
        self.assertEqual((reserva.valor_total, reserva.incluye_limpieza), (Decimal('0'), False))
        self.assertFalse(Pago.objects.filter(id_reserva_fk=reserva).exists())

    def recibir(self, reserva, faltan_sillas=0, danadas=0, limpia='si'):
        self.entrar(self.vigilante)
        datos = {f'faltan_{self.parrilla.pk}': 0, f'danados_{self.parrilla.pk}': 0,
                 f'faltan_{self.sillas.pk}': faltan_sillas, f'danados_{self.sillas.pk}': danadas,
                 'observaciones_entrega': ''}
        if limpia is not None:
            datos['zona_limpia'] = limpia
        return self.client.post(reverse('recibir_zona', args=[reserva.pk]), datos)

    def reserva_que_ya_empezo(self, limpieza=False):
        reserva = Reservas.objects.create(id_zona_fk=self.bbq, id_unidad_fk=self.unidad, reservado_por=self.usuario_res,
                                          fecha_inicio=timezone.now() - timedelta(hours=5),
                                          fecha_fin=timezone.now() - timedelta(hours=1), estado='Aprobada',
                                          incluye_limpieza=limpieza)
        reserva.calcular_cobro()
        reserva.save()
        return reserva

    def test_entrega_completa_sin_multa(self):
        reserva = self.reserva_que_ya_empezo()
        self.entrar(self.vigilante)
        self.assertContains(self.client.get(reverse('lista_entregas')), 'Recibir zona')
        self.assertRedirects(self.recibir(reserva), reverse('lista_entregas'))
        reserva.refresh_from_db()
        self.assertEqual((reserva.estado, reserva.valor_multa, reserva.recibida_por), ('Finalizada', Decimal('0'), self.vigilante))
        self.assertEqual(reserva.items_entregados.count(), 2)
        self.assertFalse(Pago.objects.filter(id_reserva_fk=reserva, tipo_pago='Multa').exists())
        # Ya no se puede volver a recibir ni editar
        self.client.get(reverse('recibir_zona', args=[reserva.pk]))
        self.assertEqual(reserva.items_entregados.count(), 2)

    def test_faltantes_danados_y_zona_sucia_generan_multa(self):
        reserva = self.reserva_que_ya_empezo(limpieza=False)
        self.recibir(reserva, faltan_sillas=1, danadas=2, limpia='no')
        reserva.refresh_from_db()
        # 3 sillas × 45.000 + limpieza no tomada 30.000
        self.assertEqual(reserva.valor_multa, Decimal('165000'))
        multa = Pago.objects.get(id_reserva_fk=reserva, tipo_pago='Multa')
        self.assertEqual((multa.valor, multa.id_residente_fk), (Decimal('165000'), self.residente))

    def test_con_limpieza_incluida_no_se_revisa_el_aseo(self):
        reserva = self.reserva_que_ya_empezo(limpieza=True)
        self.entrar(self.vigilante)
        self.assertNotIn('zona_limpia', self.client.get(reverse('recibir_zona', args=[reserva.pk])).context['form'].fields)
        self.recibir(reserva, limpia=None)
        reserva.refresh_from_db()
        self.assertEqual(reserva.valor_multa, Decimal('0'))

    def test_no_se_pueden_contar_mas_de_los_prestados(self):
        reserva = self.reserva_que_ya_empezo()
        respuesta = self.recibir(reserva, faltan_sillas=10, danadas=10)
        self.assertEqual(respuesta.status_code, 200)
        reserva.refresh_from_db()
        self.assertFalse(reserva.entregada)

    def test_no_se_recibe_una_reserva_que_no_ha_empezado(self):
        reserva = self.aprobar(self.reservar())
        self.recibir(reserva)
        reserva.refresh_from_db()
        self.assertFalse(reserva.entregada)

    def test_comprobante_pdf(self):
        reserva = self.reserva_que_ya_empezo()
        self.recibir(reserva, faltan_sillas=1)
        self.entrar(self.usuario_res)
        respuesta = self.client.get(reverse('comprobante_reserva', args=[reserva.pk]))
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertTrue(respuesta.content.startswith(b'%PDF'))
        # Otro residente no puede descargar el comprobante ajeno
        self.entrar(self.otro_usuario)
        self.assertEqual(self.client.get(reverse('comprobante_reserva', args=[reserva.pk])).status_code, 404)

    def test_admin_edita_inventario_y_precios_de_la_zona(self):
        self.entrar(self.admin)
        url = reverse('editar_zona', args=[self.bbq.pk])
        self.assertContains(self.client.get(url), 'Parrilla a gas')
        datos = {
            'nombre': 'Zona BBQ', 'capacidad': 20, 'estado': 1, 'valor_hora': '20000', 'ofrece_limpieza': 'on',
            'valor_limpieza': '35000',
            'inventario-TOTAL_FORMS': 3, 'inventario-INITIAL_FORMS': 2, 'inventario-MIN_NUM_FORMS': 0,
            'inventario-MAX_NUM_FORMS': 1000,
            'inventario-0-id_item': self.parrilla.pk, 'inventario-0-nombre': 'Parrilla a gas', 'inventario-0-cantidad': 1,
            'inventario-0-valor_reposicion': '1500000',
            'inventario-1-id_item': self.sillas.pk, 'inventario-1-nombre': 'Sillas', 'inventario-1-cantidad': 16,
            'inventario-1-valor_reposicion': '45000', 'inventario-1-DELETE': 'on',
            'inventario-2-nombre': 'Pinzas', 'inventario-2-cantidad': 2, 'inventario-2-valor_reposicion': '25000',
        }
        self.assertRedirects(self.client.post(url, datos), reverse('lista_zonas'))
        self.bbq.refresh_from_db()
        self.assertEqual(self.bbq.valor_hora, Decimal('20000'))
        self.assertEqual(sorted(self.bbq.inventario.values_list('nombre', flat=True)), ['Parrilla a gas', 'Pinzas'])

    def test_seguridad_y_residente_permisos(self):
        self.entrar(self.usuario_res)
        self.assertEqual(self.client.get(reverse('lista_entregas')).status_code, 403)
        self.entrar(self.vigilante)
        self.assertEqual(self.client.get(reverse('lista_entregas')).status_code, 200)
        self.assertEqual(self.client.get(reverse('editar_zona', args=[self.bbq.pk])).status_code, 403)

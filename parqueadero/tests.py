from datetime import datetime, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from usuarios.tests import BaseConjunto
from vehiculos.models import Vehiculos
from visitantes.models import Visitantes
from .models import ParqueoVisitante, TarifaParqueadero, calcular_cobro


class CalculoCobroTests(BaseConjunto):
    """2 horas gratis y después cada hora iniciada se cobra completa."""

    def cobro(self, minutos, valor=2000, gratis=2):
        inicio = timezone.make_aware(datetime(2026, 10, 26, 8, 0))
        return calcular_cobro(inicio, inicio + timedelta(minutes=minutos), Decimal(valor), gratis)

    def test_dentro_de_las_horas_gratis_no_paga(self):
        for minutos in (0, 30, 60, 119, 120):
            with self.subTest(minutos=minutos):
                self.assertEqual(self.cobro(minutos)[2], 0)

    def test_cada_hora_iniciada_cuenta_completa(self):
        casos = {121: 1, 130: 1, 180: 1, 181: 2, 240: 2, 241: 3}
        for minutos, horas in casos.items():
            with self.subTest(minutos=minutos):
                _, cobradas, valor = self.cobro(minutos)
                self.assertEqual(cobradas, horas)
                self.assertEqual(valor, Decimal(2000) * horas)

    def test_sin_horas_gratis(self):
        self.assertEqual(self.cobro(10, gratis=0)[1:], (1, Decimal(2000)))

    def test_segundos_sueltos_no_cuentan_como_hora(self):
        inicio = timezone.now()
        self.assertEqual(calcular_cobro(inicio, inicio + timedelta(hours=2, seconds=30), Decimal(2000), 2)[1], 0)


class ParqueaderoTests(BaseConjunto):

    def datos(self, **extra):
        datos = {'tipo_vehiculo': 'Carro', 'placa': 'abc-123', 'id_unidad_fk': self.unidad.pk,
                 'conductor': 'Ana Pérez', 'observaciones': ''}
        datos.update(extra)
        return datos

    def test_pantallas(self):
        parqueo = ParqueoVisitante.objects.create(placa='AAA111', id_unidad_fk=self.unidad,
                                                  valor_hora=2000, horas_gratis=2)
        for usuario in (self.vigilante, self.admin):
            self.entrar(usuario)
            for url in (reverse('lista_parqueos'), reverse('crear_parqueo'),
                        reverse('editar_parqueo', args=[parqueo.pk]), reverse('salida_parqueo', args=[parqueo.pk])):
                with self.subTest(usuario=usuario.username, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(reverse('editar_tarifa')).status_code, 200)

    def test_prohibido_para_residente_y_tarifa_solo_admin(self):
        self.entrar(self.usuario_res)
        for ruta in ('lista_parqueos', 'crear_parqueo', 'editar_tarifa'):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 403)
        self.entrar(self.vigilante)
        self.assertEqual(self.client.get(reverse('editar_tarifa')).status_code, 403)

    def test_registrar_ingreso_copia_la_tarifa_vigente(self):
        tarifa = TarifaParqueadero.vigente()
        tarifa.valor_hora, tarifa.horas_gratis = Decimal('3500'), 1
        tarifa.save()
        self.entrar(self.vigilante)
        respuesta = self.client.post(reverse('crear_parqueo'), self.datos())
        self.assertRedirects(respuesta, reverse('lista_parqueos'))
        parqueo = ParqueoVisitante.objects.get()
        self.assertEqual(parqueo.placa, 'ABC123')
        self.assertEqual((parqueo.valor_hora, parqueo.horas_gratis), (Decimal('3500'), 1))
        self.assertEqual(parqueo.estado, 'Dentro')
        self.assertEqual(parqueo.registrado_por, self.vigilante)

        # Cambiar la tarifa después no afecta al que ya entró
        tarifa.valor_hora = Decimal('9000')
        tarifa.save()
        parqueo.refresh_from_db()
        self.assertEqual(parqueo.valor_hora, Decimal('3500'))

    def test_validaciones_de_placa(self):
        self.entrar(self.vigilante)
        casos = {
            'placa de carro inválida': self.datos(placa='AB1234'),
            'placa de moto inválida': self.datos(tipo_vehiculo='Moto', placa='ABC123'),
            'sin unidad ni visitante': self.datos(id_unidad_fk=''),
        }
        for nombre, datos in casos.items():
            with self.subTest(caso=nombre):
                self.assertEqual(self.client.post(reverse('crear_parqueo'), datos).status_code, 200)
        self.assertFalse(ParqueoVisitante.objects.exists())

        # No puede entrar dos veces la misma placa sin haber salido
        self.client.post(reverse('crear_parqueo'), self.datos())
        self.assertEqual(self.client.post(reverse('crear_parqueo'), self.datos()).status_code, 200)
        self.assertEqual(ParqueoVisitante.objects.count(), 1)

        # Los vehículos de residentes no se cobran como visitantes
        Vehiculos.objects.create(placa='RES123', tipo_vehiculo='Carro', id_residente_fk=self.residente)
        self.assertEqual(self.client.post(reverse('crear_parqueo'), self.datos(placa='RES123')).status_code, 200)

    def test_vincular_visitante_toma_su_unidad(self):
        visitante = Visitantes.objects.create(nombre='Carlos', apellidos='Díaz', num_documento='999',
                                              id_residente_fk=self.otro, estado='Dentro',
                                              fecha_ingreso=timezone.now())
        self.entrar(self.vigilante)
        self.assertContains(self.client.get(reverse('crear_parqueo') + f'?visitante={visitante.pk}'), 'Carlos')
        self.client.post(reverse('crear_parqueo'), self.datos(id_unidad_fk='', visitante=visitante.pk, conductor=''))
        parqueo = ParqueoVisitante.objects.get()
        self.assertEqual(parqueo.id_unidad_fk, self.unidad2)
        self.assertEqual(parqueo.conductor, 'Carlos Díaz')

    def test_salida_calcula_y_guarda_el_cobro(self):
        parqueo = ParqueoVisitante.objects.create(
            placa='XYZ987', id_unidad_fk=self.unidad, valor_hora=Decimal('2000'), horas_gratis=2,
            fecha_ingreso=timezone.now() - timedelta(hours=3, minutes=10),
        )
        self.entrar(self.vigilante)
        pagina = self.client.get(reverse('salida_parqueo', args=[parqueo.pk]))
        self.assertContains(pagina, '$4.000')  # 3 h 10 min = 4 horas iniciadas - 2 gratis = 2 horas

        self.client.post(reverse('salida_parqueo', args=[parqueo.pk]))
        parqueo.refresh_from_db()
        self.assertEqual(parqueo.estado, 'Salió')
        self.assertEqual(parqueo.horas_cobradas, 2)
        self.assertEqual(parqueo.valor_cobrado, Decimal('4000'))
        self.assertEqual(parqueo.salida_por, self.vigilante)
        self.assertIsNotNone(parqueo.fecha_salida)

        # Repetir la salida no vuelve a cobrar, y ya no se puede editar
        salida = parqueo.fecha_salida
        self.client.post(reverse('salida_parqueo', args=[parqueo.pk]))
        parqueo.refresh_from_db()
        self.assertEqual(parqueo.fecha_salida, salida)
        self.assertEqual(self.client.get(reverse('editar_parqueo', args=[parqueo.pk])).status_code, 404)

    def test_admin_cambia_la_tarifa(self):
        self.entrar(self.admin)
        self.client.post(reverse('editar_tarifa'), {'valor_hora': '2500', 'horas_gratis': '1'})
        tarifa = TarifaParqueadero.vigente()
        self.assertEqual((tarifa.valor_hora, tarifa.horas_gratis), (Decimal('2500'), 1))
        self.assertEqual(self.client.post(reverse('editar_tarifa'),
                                          {'valor_hora': '-1', 'horas_gratis': '1'}).status_code, 200)

    def test_panel_de_seguridad_muestra_contador(self):
        ParqueoVisitante.objects.create(placa='CON123', id_unidad_fk=self.unidad, valor_hora=2000, horas_gratis=2)
        self.entrar(self.vigilante)
        pagina = self.client.get(reverse('dashboard'))
        self.assertContains(pagina, 'CON123')
        self.assertContains(pagina, 'data-contador')

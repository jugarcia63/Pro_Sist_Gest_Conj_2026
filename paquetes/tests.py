from django.urls import reverse

from residentes.models import Residentes
from usuarios.models import Usuario
from usuarios.tests import CLAVE, BaseConjunto
from .models import Paquete


class PaquetesTests(BaseConjunto):

    def nuevo(self, **extra):
        datos = {'numero_guia': 'GUIA1', 'destinatario': 'Laura Gómez', 'id_unidad_fk': self.unidad}
        datos.update(extra)
        return Paquete.objects.create(**datos)

    def test_pantallas_por_rol(self):
        paquete = self.nuevo()
        for usuario in (self.vigilante, self.admin):
            self.entrar(usuario)
            for url in (reverse('lista_paquetes'), reverse('crear_paquete'),
                        reverse('editar_paquete', args=[paquete.pk]), reverse('entregar_paquete', args=[paquete.pk])):
                with self.subTest(usuario=usuario.username, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)
        self.entrar(self.usuario_res)
        self.assertEqual(self.client.get(reverse('mis_paquetes')).status_code, 200)
        for ruta in ('lista_paquetes', 'crear_paquete'):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 403)
        self.entrar(self.vigilante)
        self.assertEqual(self.client.get(reverse('mis_paquetes')).status_code, 403)

    def test_registrar_paquete(self):
        self.entrar(self.vigilante)
        respuesta = self.client.post(reverse('crear_paquete'), {
            'numero_guia': ' 7000 4512 ', 'empresa': 'Servientrega', 'destinatario': '  Laura   Gómez ',
            'id_unidad_fk': self.unidad.pk, 'descripcion': 'Caja',
        })
        self.assertRedirects(respuesta, reverse('lista_paquetes'))
        paquete = Paquete.objects.get()
        self.assertEqual(paquete.numero_guia, '70004512')
        self.assertEqual(paquete.destinatario, 'Laura Gómez')
        self.assertEqual(paquete.estado, 'En recepción')
        self.assertEqual(paquete.recibido_por, self.vigilante)

        # La misma guía no puede estar dos veces en recepción
        repetido = self.client.post(reverse('crear_paquete'), {
            'numero_guia': '70004512', 'destinatario': 'Laura', 'id_unidad_fk': self.unidad.pk,
        })
        self.assertEqual(repetido.status_code, 200)
        self.assertEqual(Paquete.objects.count(), 1)

    def test_entregar_paquete(self):
        paquete = self.nuevo()
        self.entrar(self.vigilante)
        # Sin nombre de quien recibe no se entrega
        self.assertEqual(self.client.post(reverse('entregar_paquete', args=[paquete.pk]),
                                          {'entregado_a': ' '}).status_code, 200)
        respuesta = self.client.post(reverse('entregar_paquete', args=[paquete.pk]),
                                     {'entregado_a': 'Carlos Gómez', 'documento_entrega': '1234'})
        self.assertRedirects(respuesta, reverse('lista_paquetes'))
        paquete.refresh_from_db()
        self.assertEqual(paquete.estado, 'Entregado')
        self.assertEqual(paquete.entregado_a, 'Carlos Gómez')
        self.assertEqual(paquete.entregado_por, self.vigilante)
        self.assertIsNotNone(paquete.fecha_entrega)

        # Ya entregado: se ve el detalle, no se puede editar ni volver a entregar
        self.assertContains(self.client.get(reverse('entregar_paquete', args=[paquete.pk])), 'Carlos Gómez')
        self.assertEqual(self.client.get(reverse('editar_paquete', args=[paquete.pk])).status_code, 404)
        fecha = paquete.fecha_entrega
        self.client.post(reverse('entregar_paquete', args=[paquete.pk]), {'entregado_a': 'Otra persona'})
        paquete.refresh_from_db()
        self.assertEqual((paquete.entregado_a, paquete.fecha_entrega), ('Carlos Gómez', fecha))

    def test_residente_ve_los_paquetes_de_su_unidad(self):
        # Otra persona que vive en la misma unidad también ve el paquete
        companero = Usuario.objects.create_user('sofia', 'sofia@correo.co', CLAVE, rol='residente')
        Residentes.objects.create(nombres='Sofía', apellidos='Gómez', num_documento='5566',
                                  id_unidad_fk=self.unidad, usuario=companero)
        self.nuevo(numero_guia='MIO1')
        self.nuevo(numero_guia='ENTREGADO1', estado='Entregado', entregado_a='Laura')
        self.nuevo(numero_guia='AJENO1', destinatario='Pedro Ruiz', id_unidad_fk=self.unidad2)

        for usuario in (self.usuario_res, companero):
            self.entrar(usuario)
            panel = self.client.get(reverse('dashboard'))
            with self.subTest(usuario=usuario.username):
                self.assertEqual(panel.context['total_paquetes'], 1)
                self.assertContains(panel, 'MIO1')
                self.assertNotContains(panel, 'AJENO1')
                self.assertNotContains(panel, 'ENTREGADO1')
                historial = self.client.get(reverse('mis_paquetes'))
                self.assertContains(historial, 'ENTREGADO1')
                self.assertNotContains(historial, 'AJENO1')

        self.entrar(self.otro_usuario)
        self.assertEqual(self.client.get(reverse('dashboard')).context['total_paquetes'], 1)

    def test_residente_sin_unidad_no_ve_paquetes(self):
        self.residente.id_unidad_fk = None
        self.residente.save()
        self.nuevo()
        self.entrar(self.usuario_res)
        self.assertEqual(self.client.get(reverse('dashboard')).context['total_paquetes'], 0)
        self.assertEqual(self.client.get(reverse('mis_paquetes')).status_code, 200)

    def test_unidad_con_paquetes_no_se_elimina(self):
        self.residente.id_unidad_fk = None
        self.residente.save()
        self.nuevo()
        self.entrar(self.admin)
        self.client.post(reverse('eliminar_unidad', args=[self.unidad.pk]))
        self.assertTrue(type(self.unidad).objects.filter(pk=self.unidad.pk).exists())

    def test_guardia_con_paquetes_se_desactiva_en_vez_de_borrarse(self):
        self.nuevo(recibido_por=self.vigilante)
        self.entrar(self.admin)
        self.client.post(reverse('eliminar_guardia', args=[self.vigilante.pk]))
        self.vigilante.refresh_from_db()
        self.assertFalse(self.vigilante.is_active)

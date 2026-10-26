from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaPaquetes.as_view(), name='lista_paquetes'),
    path('mios/', views.MisPaquetes.as_view(), name='mis_paquetes'),
    path('nuevo/', views.CrearPaquete.as_view(), name='crear_paquete'),
    path('editar/<int:id_paquete>/', views.EditarPaquete.as_view(), name='editar_paquete'),
    path('entregar/<int:id_paquete>/', views.entregar_paquete, name='entregar_paquete'),
]

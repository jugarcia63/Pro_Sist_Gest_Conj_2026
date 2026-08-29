from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaVehiculos.as_view(), name='lista_vehiculos'),
    path('nuevo/', views.CrearVehiculo.as_view(), name='crear_vehiculo'),
    path('editar/<int:id_vehiculo>/', views.EditarVehiculo.as_view(), name='editar_vehiculo'),
]
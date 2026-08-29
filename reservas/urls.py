from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaReservas.as_view(), name='lista_reservas'),
    path('zonas/', views.ListaZonas.as_view(), name='lista_zonas'),
    path('nueva/', views.CrearReserva.as_view(), name='crear_reserva'),
    path('editar/<int:id_reservas>/', views.EditarReserva.as_view(), name='editar_reserva'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaReservas.as_view(), name='lista_reservas'),
    path('nueva/', views.CrearReserva.as_view(), name='crear_reserva'),
    path('editar/<int:id_reservas>/', views.EditarReserva.as_view(), name='editar_reserva'),
    path('estado/<int:id_reservas>/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),

    path('zonas/', views.ListaZonas.as_view(), name='lista_zonas'),
    path('zonas/nueva/', views.CrearZona.as_view(), name='crear_zona'),
    path('zonas/editar/<int:id_zona>/', views.EditarZona.as_view(), name='editar_zona'),
    path('zonas/eliminar/<int:id_zona>/', views.eliminar_zona, name='eliminar_zona'),
]

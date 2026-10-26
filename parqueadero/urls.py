from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaParqueos.as_view(), name='lista_parqueos'),
    path('nuevo/', views.CrearParqueo.as_view(), name='crear_parqueo'),
    path('editar/<int:id_parqueo>/', views.EditarParqueo.as_view(), name='editar_parqueo'),
    path('salida/<int:id_parqueo>/', views.salida_parqueo, name='salida_parqueo'),
    path('tarifa/', views.editar_tarifa, name='editar_tarifa'),
]

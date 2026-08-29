from django.urls import path
from . import views

urlpatterns = [
    path('mis-pagos/', views.ListaPagosResidente.as_view(), name='lista_pagos_residente'),
    path('admin/pagos/', views.ListaPagosAdmin.as_view(), name='lista_pagos_admin'),
    path('crear/', views.CrearPago.as_view(), name='crear_pago'),
    path('pagar/<int:pk>/', views.pasarela_pago, name='pasarela_pago'),
]
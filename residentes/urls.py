from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaResidentes.as_view(), name='lista_residentes'),
    path('nuevo/', views.CrearResidente.as_view(), name='crear_residente'),
    path('editar/<int:id_residente>/', views.EditarResidente.as_view(), name='editar_residente'),
    path('eliminar/<int:id_residente>/', views.eliminar_residente, name='eliminar_residente'),
    path('resetear-password/<int:id_residente>/', views.resetear_password, name='resetear_password'),
]
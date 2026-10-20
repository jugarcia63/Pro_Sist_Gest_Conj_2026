from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaResidentes.as_view(), name='lista_residentes'),
    path('nuevo/', views.CrearResidente.as_view(), name='crear_residente'),
    path('editar/<int:id_residente>/', views.EditarResidente.as_view(), name='editar_residente'),
    path('eliminar/<int:id_residente>/', views.eliminar_residente, name='eliminar_residente'),

    path('unidades/', views.ListaUnidades.as_view(), name='lista_unidades'),
    path('unidades/nueva/', views.CrearUnidad.as_view(), name='crear_unidad'),
    path('unidades/editar/<int:id_unidad>/', views.EditarUnidad.as_view(), name='editar_unidad'),
    path('unidades/eliminar/<int:id_unidad>/', views.eliminar_unidad, name='eliminar_unidad'),
]

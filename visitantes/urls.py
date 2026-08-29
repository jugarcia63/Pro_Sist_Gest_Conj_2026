from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaVisitantes.as_view(), name='lista_visitantes'),
    path('nuevo/', views.CrearVisitante.as_view(), name='crear_visitante'),
    path('editar/<int:id_visitante>/', views.EditarVisitante.as_view(), name='editar_visitante'),
]
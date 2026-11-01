from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_avisos, name='lista_avisos'),
    path('<int:id_aviso>/', views.abrir_aviso, name='abrir_aviso'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.CrearReporte.as_view(), name='crear_reporte'),
    path('mis-reportes/', views.MisReportes.as_view(), name='mis_reportes'),
    path('admin/reportes/', views.ListaReportesAdmin.as_view(), name='lista_reportes_admin'),
    path('cambiar-estado/<int:pk>/', views.cambiar_estado, name='cambiar_estado_reporte'),
]
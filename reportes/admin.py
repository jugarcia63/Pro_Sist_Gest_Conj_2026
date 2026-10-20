from django.contrib import admin
from .models import ReporteDano


@admin.register(ReporteDano)
class ReporteDanoAdmin(admin.ModelAdmin):
    list_display = ['id_reportes', 'id_residente_fk', 'categoria', 'torre', 'piso', 'estado', 'fecha_reporte']
    list_filter = ['estado', 'categoria']

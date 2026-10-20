from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id_pago', 'id_residente_fk', 'tipo_pago', 'mes_ano', 'valor', 'fecha_vencimiento', 'estado']
    list_filter = ['estado', 'tipo_pago']

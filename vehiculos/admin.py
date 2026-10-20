from django.contrib import admin
from .models import Vehiculos


@admin.register(Vehiculos)
class VehiculosAdmin(admin.ModelAdmin):
    list_display = ['placa', 'tipo_vehiculo', 'marca', 'modelo', 'color', 'id_residente_fk', 'estado']
    search_fields = ['placa']

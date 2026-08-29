from django import forms
from .models import Vehiculos

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculos
        fields = ['placa', 'marca', 'modelo', 'color', 'id_residente_fk', 'tipo_vehiculo', 'estado']
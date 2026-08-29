from django import forms
from .models import Visitantes

class VisitanteForm(forms.ModelForm):
    class Meta:
        model = Visitantes
        fields = ['nombre', 'apellidos', 'tipo_documento', 'num_documento', 'telefono', 'motivo', 'id_residente_fk', 'fecha_ingreso', 'fecha_salida', 'estado']
        widgets = {
            'fecha_ingreso': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
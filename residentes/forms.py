from django import forms
from .models import Residentes

class ResidenteForm(forms.ModelForm):
    class Meta:
        model = Residentes
        fields = ['tipo_documento', 'num_documento', 'nombres', 'apellidos', 'telefono', 'email', 'id_unidad_fk']
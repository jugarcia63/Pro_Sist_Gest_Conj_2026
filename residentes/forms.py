from django import forms
from validadores import ValidacionLetrasNumerosMixin
from .models import Residentes


class ResidenteForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    campos_solo_letras = ['nombres', 'apellidos', 'tipo_documento']
    campos_solo_numeros = ['num_documento', 'telefono']

    class Meta:
        model = Residentes
        fields = ['tipo_documento', 'num_documento', 'nombres', 'apellidos', 'telefono', 'email', 'id_unidad_fk']
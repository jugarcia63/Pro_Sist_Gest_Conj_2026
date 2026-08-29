from django import forms
from validadores import ValidacionLetrasNumerosMixin
from .models import ReporteDano


class ReporteDanoForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    campos_solo_letras = ['categoria', 'torre']
    campos_solo_numeros = ['piso']
    # descripcion se deja libre (texto largo, ya tiene su propia validación de longitud)

    class Meta:
        model = ReporteDano
        fields = ['categoria', 'descripcion', 'torre', 'piso']

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        if descripcion and len(descripcion.strip()) < 10:
            raise forms.ValidationError("La descripción debe tener al menos 10 caracteres.")
        return descripcion
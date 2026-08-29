from django import forms
from .models import ReporteDano

class ReporteDanoForm(forms.ModelForm):
    class Meta:
        model = ReporteDano
        fields = ['categoria', 'descripcion', 'torre', 'piso']

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        if descripcion and len(descripcion.strip()) < 10:
            raise forms.ValidationError("La descripción debe tener al menos 10 caracteres.")
        return descripcion
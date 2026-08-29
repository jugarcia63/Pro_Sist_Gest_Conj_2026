from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Pago

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['id_residente_fk', 'tipo_pago', 'id_reserva_fk', 'mes_ano',
                  'valor', 'fecha_vencimiento', 'metodo_pago', 'estado']
        widgets = {
            'mes_ano': forms.DateInput(attrs={'type': 'month'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is not None and valor <= 0:
            raise ValidationError("El valor de la factura debe ser mayor a cero.")
        return valor

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get('fecha_vencimiento')
        if fecha and fecha < timezone.now().date():
            raise ValidationError("La fecha de vencimiento no puede ser en el pasado.")
        return fecha
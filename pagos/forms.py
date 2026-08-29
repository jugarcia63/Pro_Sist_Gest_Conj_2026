from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Pago


class MesAnoWidget(forms.DateInput):
    """Convierte el valor 'YYYY-MM' del input type=month en 'YYYY-MM-01' antes de que Django lo valide."""
    input_type = 'month'

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value:
            return value + '-01'
        return value


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        # El admin ya NO puede fijar 'estado' ni 'metodo_pago' — eso lo controla el residente al pagar
        fields = ['id_residente_fk', 'tipo_pago', 'id_reserva_fk', 'mes_ano', 'valor', 'fecha_vencimiento']
        widgets = {
            'mes_ano': MesAnoWidget(format='%Y-%m-%d'),
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


class PasarelaPagoForm(forms.Form):
    """Formulario ficticio de tarjeta — solo para simular la experiencia de pago, no procesa nada real."""
    nombre_titular = forms.CharField(label='Nombre del titular', max_length=100)
    numero_tarjeta = forms.CharField(label='Número de tarjeta', max_length=19,
                                      widget=forms.TextInput(attrs={'placeholder': '4111 1111 1111 1111'}))
    fecha_expiracion = forms.CharField(label='Vencimiento (MM/AA)', max_length=5,
                                        widget=forms.TextInput(attrs={'placeholder': '12/28'}))
    cvv = forms.CharField(label='CVV', max_length=4, widget=forms.PasswordInput())

    def clean_numero_tarjeta(self):
        numero = self.cleaned_data.get('numero_tarjeta', '').replace(' ', '')
        if not numero.isdigit() or len(numero) not in (15, 16):
            raise ValidationError("Ingresa un número de tarjeta válido (15 o 16 dígitos).")
        return numero

    def clean_fecha_expiracion(self):
        import re
        fecha = self.cleaned_data.get('fecha_expiracion', '')
        if not re.match(r'^\d{2}/\d{2}$', fecha):
            raise ValidationError("Formato inválido. Usa MM/AA, ej: 12/28.")
        return fecha

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv', '')
        if not cvv.isdigit() or len(cvv) not in (3, 4):
            raise ValidationError("El CVV debe tener 3 o 4 dígitos.")
        return cvv
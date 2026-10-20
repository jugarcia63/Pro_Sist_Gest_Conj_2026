import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from residentes.forms import ResidenteChoiceField
from .models import Pago
from django.utils.translation import gettext_lazy as _

TIPOS_PAGO = [
    ('Administración', _('Cuota de administración')),
    ('Reserva', _('Reserva de zona común')),
    ('Multa', _('Multa')),
    ('Parqueadero', _('Parqueadero')),
    ('Otro', _('Otro')),
]


class MesAnoWidget(forms.DateInput):
    """Input type=month: convierte 'YYYY-MM' en 'YYYY-MM-01' para Django, y al revés para mostrarlo."""
    input_type = 'month'

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value and len(value) == 7:
            return value + '-01'
        return value

    def format_value(self, value):
        value = super().format_value(value)
        return value[:7] if value else value


class PagoForm(forms.ModelForm):
    tipo_pago = forms.ChoiceField(choices=TIPOS_PAGO, label=_('Concepto'))
    id_residente_fk = ResidenteChoiceField(label=_('Residente'))

    class Meta:
        model = Pago
        # El admin NO puede fijar 'estado' ni 'metodo_pago': eso pasa cuando el residente paga
        fields = ['id_residente_fk', 'tipo_pago', 'id_reserva_fk', 'mes_ano', 'valor', 'fecha_vencimiento']
        labels = {
            'id_reserva_fk': _('Reserva asociada (opcional)'),
            'mes_ano': _('Mes que se cobra'),
            'valor': _('Valor (COP)'),
            'fecha_vencimiento': _('Fecha límite de pago'),
        }
        widgets = {
            'mes_ano': MesAnoWidget(format='%Y-%m-%d'),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'valor': forms.NumberInput(attrs={'step': '1000', 'min': '0', 'placeholder': '320000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_reserva_fk'].queryset = (self.fields['id_reserva_fk'].queryset
                                                 .select_related('id_zona_fk').order_by('-fecha_inicio'))
        self.fields['id_reserva_fk'].empty_label = _('Ninguna')
        if not self.is_bound and not self.instance.pk:
            hoy = timezone.localdate()
            self.initial.setdefault('mes_ano', hoy.replace(day=1))

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is not None and valor <= 0:
            raise ValidationError(_('El valor de la factura debe ser mayor a cero.'))
        return valor

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get('fecha_vencimiento')
        if fecha and fecha < timezone.localdate():
            raise ValidationError(_('La fecha límite no puede estar en el pasado.'))
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('tipo_pago') == 'Reserva' and not cleaned_data.get('id_reserva_fk'):
            self.add_error('id_reserva_fk', _('Selecciona la reserva que se está cobrando.'))
        return cleaned_data


def _luhn_valido(numero):
    """Verificación estándar de los números de tarjeta (algoritmo de Luhn)."""
    total = 0
    for i, digito in enumerate(reversed(numero)):
        d = int(digito)
        if i % 2 == 1:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


class PasarelaPagoForm(forms.Form):
    """Formulario ficticio de tarjeta: solo simula la experiencia de pago, no procesa ni guarda nada real."""
    nombre_titular = forms.CharField(label=_('Nombre del titular'), max_length=100,
                                     widget=forms.TextInput(attrs={'autocomplete': 'cc-name', 'placeholder': _('Como aparece en la tarjeta')}))
    numero_tarjeta = forms.CharField(label=_('Número de tarjeta'), max_length=19,
                                     widget=forms.TextInput(attrs={'placeholder': '4111 1111 1111 1111',
                                                                   'inputmode': 'numeric', 'autocomplete': 'cc-number'}))
    fecha_expiracion = forms.CharField(label=_('Vencimiento (MM/AA)'), max_length=5,
                                       widget=forms.TextInput(attrs={'placeholder': '12/28', 'inputmode': 'numeric',
                                                                     'autocomplete': 'cc-exp'}))
    cvv = forms.CharField(label=_('CVV'), max_length=4,
                          widget=forms.PasswordInput(attrs={'inputmode': 'numeric', 'autocomplete': 'cc-csc', 'placeholder': '•••'}))

    def clean_numero_tarjeta(self):
        numero = self.cleaned_data.get('numero_tarjeta', '').replace(' ', '').replace('-', '')
        if not numero.isdigit() or len(numero) not in (15, 16):
            raise ValidationError(_('Ingresa un número de tarjeta válido (15 o 16 dígitos).'))
        if not _luhn_valido(numero):
            raise ValidationError(_('El número de tarjeta no es válido. Revisa los dígitos.'))
        return numero

    def clean_fecha_expiracion(self):
        fecha = self.cleaned_data.get('fecha_expiracion', '').strip()
        coincidencia = re.match(r'^(\d{2})/(\d{2})$', fecha)
        if not coincidencia:
            raise ValidationError(_('Formato inválido. Usa MM/AA, ej: 12/28.'))
        mes, anio = int(coincidencia.group(1)), 2000 + int(coincidencia.group(2))
        if not 1 <= mes <= 12:
            raise ValidationError(_('El mes debe estar entre 01 y 12.'))
        hoy = timezone.localdate()
        if (anio, mes) < (hoy.year, hoy.month):
            raise ValidationError(_('La tarjeta está vencida.'))
        return fecha

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv', '')
        if not cvv.isdigit() or len(cvv) not in (3, 4):
            raise ValidationError(_('El CVV debe tener 3 o 4 dígitos.'))
        return cvv

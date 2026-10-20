import re
from django import forms
from django.utils.translation import gettext_lazy as _

from residentes.forms import ResidenteChoiceField
from validadores import ValidacionLetrasNumerosMixin
from .models import Vehiculos

REGEX_PLACA_CARRO = re.compile(r'^[A-Z]{3}[0-9]{3}$')       # ej: ABC123
REGEX_PLACA_MOTO = re.compile(r'^[A-Z]{3}[0-9]{2}[A-Z]$')   # ej: ASD12G

ESTADOS_VEHICULO = [('Activo', _('Activo')), ('Inactivo', _('Inactivo'))]


class VehiculoForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    campos_solo_letras = ['marca', 'color']
    # placa y tipo_vehiculo se validan aparte; modelo queda libre (ej: "Corolla 2023")

    tipo_vehiculo = forms.ChoiceField(choices=[('Carro', _('Carro')), ('Moto', _('Moto'))], label=_('Tipo de vehículo'))
    estado = forms.ChoiceField(choices=ESTADOS_VEHICULO, initial='Activo', label=_('Estado'))
    id_residente_fk = ResidenteChoiceField(label=_('Propietario'))

    class Meta:
        model = Vehiculos
        fields = ['tipo_vehiculo', 'placa', 'marca', 'modelo', 'color', 'id_residente_fk', 'estado']
        labels = {'placa': _('Placa'), 'marca': _('Marca'), 'modelo': _('Modelo'), 'color': _('Color')}
        widgets = {
            'placa': forms.TextInput(attrs={'placeholder': 'ABC123', 'style': 'text-transform:uppercase'}),
        }

    def __init__(self, *args, es_residente=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['placa'].required = True
        self.fields['marca'].required = True
        if es_residente:
            # El residente siempre registra a su nombre: el propietario lo pone la vista
            del self.fields['id_residente_fk']

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_vehiculo')
        placa = (cleaned_data.get('placa') or '').upper().replace(' ', '').replace('-', '')

        if placa:
            cleaned_data['placa'] = placa
            if tipo == 'Carro' and not REGEX_PLACA_CARRO.match(placa):
                self.add_error('placa', _('Placa de carro inválida. Formato: 3 letras + 3 números (ej: ABC123).'))
            elif tipo == 'Moto' and not REGEX_PLACA_MOTO.match(placa):
                self.add_error('placa', _('Placa de moto inválida. Formato: 3 letras + 2 números + 1 letra (ej: ASD12G).'))
            elif Vehiculos.objects.filter(placa__iexact=placa).exclude(pk=self.instance.pk).exists():
                self.add_error('placa', _('Ya hay un vehículo registrado con esta placa.'))

        return cleaned_data

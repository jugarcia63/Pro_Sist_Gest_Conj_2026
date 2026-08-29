import re
from django import forms
from validadores import ValidacionLetrasNumerosMixin
from .models import Vehiculos

REGEX_PLACA_CARRO = re.compile(r'^[A-Za-z]{3}[0-9]{3}$')       # ej: ABC123
REGEX_PLACA_MOTO = re.compile(r'^[A-Za-z]{3}[0-9]{2}[A-Za-z]$')  # ej: ASD12G


class VehiculoForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    campos_solo_letras = ['marca', 'color', 'estado']
    # placa y tipo_vehiculo se validan aparte; modelo queda libre (ej: "Corolla 2023")

    tipo_vehiculo = forms.ChoiceField(
        choices=[('Carro', 'Carro'), ('Moto', 'Moto')],
        label='Tipo de vehículo'
    )

    class Meta:
        model = Vehiculos
        fields = ['placa', 'marca', 'modelo', 'color', 'id_residente_fk', 'tipo_vehiculo', 'estado']

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_vehiculo')
        placa = cleaned_data.get('placa')

        if placa and tipo:
            placa = placa.upper().strip()
            if tipo == 'Carro' and not REGEX_PLACA_CARRO.match(placa):
                self.add_error('placa', 'Placa de carro inválida. Formato: 3 letras + 3 números (ej: ABC123).')
            elif tipo == 'Moto' and not REGEX_PLACA_MOTO.match(placa):
                self.add_error('placa', 'Placa de moto inválida. Formato: 3 letras + 2 números + 1 letra (ej: ASD12G).')

        return cleaned_data
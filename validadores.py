import re
from django import forms

REGEX_LETRAS = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$')
REGEX_NUMEROS = re.compile(r'^[0-9]+$')


class ValidacionLetrasNumerosMixin:
    """
    Mixin para ModelForm/Form. Declara en la clase hija:
      campos_solo_letras = ['nombre', 'apellidos', ...]
      campos_solo_numeros = ['telefono', 'num_documento', ...]
    """
    campos_solo_letras = []
    campos_solo_numeros = []

    def clean(self):
        cleaned_data = super().clean()

        for campo in self.campos_solo_letras:
            valor = cleaned_data.get(campo)
            if valor and not REGEX_LETRAS.match(str(valor)):
                self.add_error(campo, 'Este campo solo permite letras.')

        for campo in self.campos_solo_numeros:
            valor = cleaned_data.get(campo)
            if valor is not None and not REGEX_NUMEROS.match(str(valor)):
                self.add_error(campo, 'Este campo solo permite números.')

        return cleaned_data
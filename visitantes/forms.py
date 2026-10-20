from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from residentes.forms import TIPOS_DOCUMENTO, ResidenteChoiceField
from validadores import ValidacionLetrasNumerosMixin
from .models import Visitantes

ESTADOS_VISITANTE = [('Dentro', _('Dentro del conjunto')), ('Salió', _('Ya salió'))]


class VisitanteForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    campos_solo_letras = ['nombre', 'apellidos']
    campos_solo_numeros = ['num_documento', 'telefono']

    tipo_documento = forms.ChoiceField(choices=TIPOS_DOCUMENTO, label=_('Tipo de documento'))
    id_residente_fk = ResidenteChoiceField(label=_('Visita a'))
    estado = forms.ChoiceField(choices=ESTADOS_VISITANTE, initial='Dentro', label=_('Estado'))

    class Meta:
        model = Visitantes
        fields = ['nombre', 'apellidos', 'tipo_documento', 'num_documento', 'telefono',
                  'id_residente_fk', 'motivo', 'fecha_ingreso', 'fecha_salida', 'estado']
        labels = {
            'nombre': _('Nombre'),
            'apellidos': _('Apellidos'),
            'num_documento': _('Número de documento'),
            'telefono': _('Teléfono'),
            'motivo': _('Motivo'),
            'fecha_ingreso': _('Ingreso'),
            'fecha_salida': _('Salida'),
        }
        widgets = {
            'fecha_ingreso': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'motivo': forms.TextInput(attrs={'placeholder': _('Ej: visita familiar, domicilio, mantenimiento')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('nombre', 'apellidos', 'num_documento', 'fecha_ingreso'):
            self.fields[campo].required = True
        if not self.instance.pk:
            self.initial.setdefault('fecha_ingreso', timezone.localtime().strftime('%Y-%m-%dT%H:%M'))

    def clean(self):
        cleaned_data = super().clean()
        ingreso = cleaned_data.get('fecha_ingreso')
        salida = cleaned_data.get('fecha_salida')
        estado = cleaned_data.get('estado')

        if ingreso and salida and salida <= ingreso:
            self.add_error('fecha_salida', _('La salida debe ser posterior al ingreso.'))
        if estado == 'Salió' and not salida:
            cleaned_data['fecha_salida'] = timezone.now()
        if estado == 'Dentro' and salida:
            self.add_error('estado', _('Si ya tiene hora de salida, el estado debe ser "Ya salió".'))
        return cleaned_data

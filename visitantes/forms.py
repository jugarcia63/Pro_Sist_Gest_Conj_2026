from datetime import timedelta

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from residentes.models import Unidades
from validadores import ValidacionLetrasNumerosMixin
from .models import Visitantes


class VisitanteForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    """Registro de ingreso de una persona: solo los datos indispensables.
    No se piden teléfono ni motivo, y no hay hora de salida."""
    campos_solo_letras = ['nombre', 'apellidos']
    campos_solo_numeros = ['num_documento']

    id_unidad_fk = forms.ModelChoiceField(
        queryset=Unidades.objects.order_by('torre', 'piso', 'apto'), label=_('Unidad que visita'),
        empty_label=_('Selecciona la torre y el apartamento'),
    )

    class Meta:
        model = Visitantes
        fields = ['nombre', 'apellidos', 'num_documento', 'fecha_ingreso', 'id_unidad_fk']
        labels = {
            'nombre': _('Nombres'),
            'apellidos': _('Apellidos'),
            'num_documento': _('Cédula'),
            'fecha_ingreso': _('Hora de entrada'),
        }
        widgets = {
            'num_documento': forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'off'}),
            'fecha_ingreso': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields:
            self.fields[campo].required = True
        if self.instance.pk and not self.instance.id_unidad_fk_id:
            self.initial['id_unidad_fk'] = getattr(self.instance.unidad_visitada, 'pk', None)
        if not self.instance.pk:
            self.initial.setdefault('fecha_ingreso', timezone.localtime().strftime('%Y-%m-%dT%H:%M'))

    def clean_fecha_ingreso(self):
        ingreso = self.cleaned_data.get('fecha_ingreso')
        if ingreso and ingreso > timezone.now() + timedelta(minutes=5):
            raise forms.ValidationError(_('La hora de entrada no puede estar en el futuro.'))
        return ingreso

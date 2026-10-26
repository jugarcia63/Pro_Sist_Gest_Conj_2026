from django import forms
from django.utils.translation import gettext_lazy as _

from validadores import ValidacionLetrasNumerosMixin
from .models import Residentes, Unidades

TIPOS_DOCUMENTO = [
    ('CC', _('Cédula de ciudadanía')),
    ('CE', _('Cédula de extranjería')),
    ('TI', _('Tarjeta de identidad')),
    ('PA', _('Pasaporte')),
]


class ResidenteChoiceField(forms.ModelChoiceField):
    """Selector de residente que muestra nombre, documento y unidad (se reutiliza en otras apps)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', Residentes.objects.select_related('id_unidad_fk').order_by('nombres', 'apellidos'))
        kwargs.setdefault('empty_label', _('Selecciona un residente'))
        super().__init__(*args, **kwargs)

    def label_from_instance(self, residente):
        unidad = residente.id_unidad_fk
        ubicacion = str(unidad) if unidad else _('Sin unidad')
        return f"{residente} · {residente.tipo_documento or ''} {residente.num_documento or '—'} · {ubicacion}"


class ResidenteForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    campos_solo_letras = ['nombres', 'apellidos']
    campos_solo_numeros = ['num_documento', 'telefono']

    tipo_documento = forms.ChoiceField(choices=TIPOS_DOCUMENTO, label=_('Tipo de documento'))
    email = forms.EmailField(
        label=_('Correo electrónico'), required=False,
    )

    class Meta:
        model = Residentes
        fields = ['nombres', 'apellidos', 'tipo_documento', 'num_documento', 'telefono', 'email', 'id_unidad_fk']
        labels = {
            'nombres': _('Nombres'),
            'apellidos': _('Apellidos'),
            'num_documento': _('Número de documento'),
            'telefono': _('Teléfono'),
            'id_unidad_fk': _('Unidad (torre y apartamento)'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('nombres', 'apellidos', 'num_documento'):
            self.fields[campo].required = True
        self.fields['id_unidad_fk'].queryset = Unidades.objects.order_by('torre', 'piso', 'apto')
        self.fields['id_unidad_fk'].empty_label = _('Sin unidad asignada')

    def clean_num_documento(self):
        numero = (self.cleaned_data.get('num_documento') or '').strip()
        repetido = Residentes.objects.filter(num_documento=numero).exclude(pk=self.instance.pk)
        if numero and repetido.exists():
            raise forms.ValidationError(_('Ya existe un residente con este número de documento.'))
        return numero

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        repetido = Residentes.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if email and repetido.exists():
            raise forms.ValidationError(_('Ya hay otro residente con este correo.'))
        return email


class UnidadForm(forms.ModelForm):
    estado = forms.TypedChoiceField(choices=[(1, _('Ocupada / activa')), (0, _('Desocupada'))], coerce=int,
                                    initial=1, label=_('Estado'))

    class Meta:
        model = Unidades
        fields = ['torre', 'apto', 'piso', 'area', 'estado']
        labels = {'torre': _('Torre'), 'apto': _('Apartamento'), 'piso': _('Piso'), 'area': _('Área (m²)')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('torre', 'apto', 'piso'):
            self.fields[campo].required = True

    def clean_torre(self):
        return (self.cleaned_data.get('torre') or '').strip().upper()

    def clean_piso(self):
        piso = self.cleaned_data.get('piso')
        if piso is not None and piso < 0:
            raise forms.ValidationError(_('El piso no puede ser negativo.'))
        return piso

    def clean_area(self):
        area = self.cleaned_data.get('area')
        if area is not None and area <= 0:
            raise forms.ValidationError(_('El área debe ser mayor a cero.'))
        return area

    def clean(self):
        cleaned_data = super().clean()
        torre, apto = cleaned_data.get('torre'), (cleaned_data.get('apto') or '').strip()
        if torre and apto:
            cleaned_data['apto'] = apto
            repetida = Unidades.objects.filter(torre__iexact=torre, apto__iexact=apto).exclude(pk=self.instance.pk)
            if repetida.exists():
                raise forms.ValidationError(_('La unidad Torre %(torre)s - Apto %(apto)s ya existe.')
                                            % {'torre': torre, 'apto': apto})
        return cleaned_data

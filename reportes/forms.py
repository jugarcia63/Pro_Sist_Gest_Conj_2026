from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ReporteDano

CATEGORIAS = [
    ('Plomería', _('Plomería (fugas, tuberías)')),
    ('Eléctrico', _('Eléctrico (luces, tomas)')),
    ('Estructural', _('Estructural (paredes, techos, humedad)')),
    ('Ascensor', _('Ascensor')),
    ('Zonas comunes', _('Zonas comunes')),
    ('Seguridad', _('Seguridad (puertas, cámaras, citófonos)')),
    ('Otro', _('Otro')),
]


class ReporteDanoForm(forms.ModelForm):
    categoria = forms.ChoiceField(choices=CATEGORIAS, label=_('Categoría'))

    class Meta:
        model = ReporteDano
        fields = ['categoria', 'torre', 'piso', 'descripcion']
        labels = {'descripcion': _('Describe el daño'), 'torre': _('Torre'), 'piso': _('Piso')}
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'rows': 5, 'placeholder': _('Qué pasó, dónde exactamente y desde cuándo. Ej: gotera en el techo del baño desde ayer.')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['torre'].required = True

    def clean_torre(self):
        torre = (self.cleaned_data.get('torre') or '').strip().upper()
        if torre and not torre.isalnum():
            raise forms.ValidationError(_('La torre solo puede tener letras o números (ej: A, 2).'))
        return torre

    def clean_piso(self):
        piso = self.cleaned_data.get('piso')
        if piso is not None and piso < 0:
            raise forms.ValidationError(_('El piso no puede ser negativo.'))
        return piso

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        if len(descripcion) < 10:
            raise forms.ValidationError(_('La descripción debe tener al menos 10 caracteres.'))
        return descripcion

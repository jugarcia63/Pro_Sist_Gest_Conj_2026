from django import forms
from django.utils.translation import gettext_lazy as _

from parqueadero.forms import UnidadChoiceField
from validadores import REGEX_NUMEROS
from .models import Paquete

EMPRESAS_SUGERIDAS = ['Servientrega', 'Coordinadora', 'Interrapidísimo', 'Envía', 'TCC', 'Deprisa',
                      '4-72', 'DHL', 'FedEx', 'Mercado Libre', 'Amazon']


class PaqueteForm(forms.ModelForm):
    id_unidad_fk = UnidadChoiceField(label=_('Unidad destino'))

    class Meta:
        model = Paquete
        fields = ['numero_guia', 'empresa', 'destinatario', 'id_unidad_fk', 'descripcion']
        labels = {
            'numero_guia': _('Número de guía'),
            'empresa': _('Transportadora'),
            'destinatario': _('Nombre del destinatario'),
            'descripcion': _('Descripción'),
        }
        widgets = {
            'numero_guia': forms.TextInput(attrs={'placeholder': _('Ej: 700045123987'), 'autocomplete': 'off'}),
            'empresa': forms.TextInput(attrs={'placeholder': _('Ej: Servientrega'), 'list': 'empresas'}),
            'destinatario': forms.TextInput(attrs={'placeholder': _('Como aparece en el paquete')}),
            'descripcion': forms.TextInput(attrs={'placeholder': _('Ej: caja mediana, sobre, bolsa')}),
        }

    def clean_numero_guia(self):
        guia = ''.join((self.cleaned_data.get('numero_guia') or '').split()).upper()
        if not guia:
            raise forms.ValidationError(_('Escribe el número de guía.'))
        repetido = Paquete.objects.filter(numero_guia__iexact=guia, estado='En recepción').exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError(_('Ya hay un paquete en recepción con esta guía.'))
        return guia

    def clean_destinatario(self):
        nombre = ' '.join((self.cleaned_data.get('destinatario') or '').split())
        if not nombre:
            raise forms.ValidationError(_('Escribe el nombre del destinatario.'))
        return nombre


class EntregaPaqueteForm(forms.ModelForm):
    class Meta:
        model = Paquete
        fields = ['entregado_a', 'documento_entrega']
        labels = {'entregado_a': _('Entregado a'), 'documento_entrega': _('Documento de quien recibe')}
        help_texts = {'entregado_a': _('Nombre de la persona que recoge el paquete en portería.')}
        widgets = {'documento_entrega': forms.TextInput(attrs={'placeholder': _('Opcional')})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['entregado_a'].required = True

    def clean_entregado_a(self):
        nombre = ' '.join((self.cleaned_data.get('entregado_a') or '').split())
        if not nombre:
            raise forms.ValidationError(_('Escribe a quién se entrega el paquete.'))
        return nombre

    def clean_documento_entrega(self):
        documento = (self.cleaned_data.get('documento_entrega') or '').strip()
        if documento and not REGEX_NUMEROS.match(documento):
            raise forms.ValidationError(_('Este campo solo permite números.'))
        return documento

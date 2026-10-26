from django import forms
from django.utils.translation import gettext_lazy as _

from residentes.models import Unidades
from vehiculos.forms import REGEX_PLACA_CARRO, REGEX_PLACA_MOTO
from vehiculos.models import Vehiculos
from visitantes.models import Visitantes
from .models import ParqueoVisitante, TarifaParqueadero


class UnidadChoiceField(forms.ModelChoiceField):
    """Selector de torre y apartamento (se reutiliza en paquetes)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', Unidades.objects.order_by('torre', 'piso', 'apto'))
        kwargs.setdefault('empty_label', _('Selecciona la unidad'))
        super().__init__(*args, **kwargs)


class VisitanteDentroChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, visitante):
        destino = visitante.id_residente_fk
        unidad = destino.id_unidad_fk if destino else None
        return f"{visitante} · {visitante.num_documento or '—'}" + (f" · {unidad}" if unidad else '')


class ParqueoForm(forms.ModelForm):
    tipo_vehiculo = forms.ChoiceField(choices=[('Carro', _('Carro')), ('Moto', _('Moto'))], label=_('Tipo de vehículo'))
    id_unidad_fk = UnidadChoiceField(
        label=_('Unidad que visita'), required=False,
        help_text=_('Si eliges el visitante, se toma la unidad a la que va.'),
    )
    visitante = VisitanteDentroChoiceField(
        queryset=Visitantes.objects.none(), required=False, label=_('Visitante (opcional)'),
        empty_label=_('Sin vincular a un visitante'),
        help_text=_('Solo aparecen los visitantes que están dentro del conjunto.'),
    )

    class Meta:
        model = ParqueoVisitante
        fields = ['tipo_vehiculo', 'placa', 'visitante', 'id_unidad_fk', 'conductor', 'observaciones']
        labels = {'placa': _('Placa'), 'conductor': _('Conductor'), 'observaciones': _('Observaciones')}
        widgets = {
            'placa': forms.TextInput(attrs={'placeholder': 'ABC123', 'style': 'text-transform:uppercase',
                                            'autocomplete': 'off'}),
            'conductor': forms.TextInput(attrs={'placeholder': _('Nombre de quien conduce')}),
            'observaciones': forms.TextInput(attrs={'placeholder': _('Ej: celda 12, rayón en la puerta')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        visitantes = Visitantes.objects.select_related('id_residente_fk__id_unidad_fk').filter(estado='Dentro')
        if self.instance.visitante_id:
            visitantes = visitantes | Visitantes.objects.filter(pk=self.instance.visitante_id)
        self.fields['visitante'].queryset = visitantes.order_by('-fecha_ingreso')

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_vehiculo')
        placa = (cleaned_data.get('placa') or '').upper().replace(' ', '').replace('-', '')
        visitante = cleaned_data.get('visitante')

        if placa:
            cleaned_data['placa'] = placa
            if tipo == 'Carro' and not REGEX_PLACA_CARRO.match(placa):
                self.add_error('placa', _('Placa de carro inválida. Formato: 3 letras + 3 números (ej: ABC123).'))
            elif tipo == 'Moto' and not REGEX_PLACA_MOTO.match(placa):
                self.add_error('placa', _('Placa de moto inválida. Formato: 3 letras + 2 números + 1 letra (ej: ASD12G).'))
            elif (ParqueoVisitante.objects.filter(placa=placa, estado='Dentro')
                  .exclude(pk=self.instance.pk).exists()):
                self.add_error('placa', _('Este vehículo ya está registrado dentro del parqueadero.'))
            elif Vehiculos.objects.filter(placa__iexact=placa).exists():
                self.add_error('placa', _('Esta placa es de un vehículo de residente; no se cobra como visitante.'))

        # Si no eligieron unidad, se toma la del residente al que va el visitante
        if not cleaned_data.get('id_unidad_fk') and visitante and visitante.id_residente_fk:
            cleaned_data['id_unidad_fk'] = visitante.id_residente_fk.id_unidad_fk
        if not cleaned_data.get('id_unidad_fk'):
            self.add_error('id_unidad_fk', _('Indica a qué unidad va el vehículo.'))

        if visitante and not (cleaned_data.get('conductor') or '').strip():
            cleaned_data['conductor'] = str(visitante)
        return cleaned_data


class TarifaForm(forms.ModelForm):
    class Meta:
        model = TarifaParqueadero
        fields = ['valor_hora', 'horas_gratis']
        labels = {'valor_hora': _('Valor por hora (COP)'), 'horas_gratis': _('Horas gratis')}
        help_texts = {
            'valor_hora': _('Se cobra por cada hora iniciada después de las horas gratis.'),
            'horas_gratis': _('Tiempo inicial sin costo. Pon 0 si se cobra desde el primer minuto.'),
        }

    def clean_valor_hora(self):
        valor = self.cleaned_data.get('valor_hora')
        if valor is not None and valor < 0:
            raise forms.ValidationError(_('El valor no puede ser negativo.'))
        return valor

    def clean_horas_gratis(self):
        horas = self.cleaned_data.get('horas_gratis')
        if horas is not None and horas > 24:
            raise forms.ValidationError(_('Máximo 24 horas gratis.'))
        return horas

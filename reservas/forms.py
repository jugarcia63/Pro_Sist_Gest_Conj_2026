from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from residentes.models import Unidades
from .models import ItemInventario, Reservas, ZonasComunes
from django.utils.translation import gettext_lazy as _

ESTADOS_RESERVA = [
    ('Pendiente', _('Pendiente')),
    ('Aprobada', _('Aprobada')),
    ('Rechazada', _('Rechazada')),
    ('Cancelada', _('Cancelada')),
]
# Estas reservas ya no ocupan el horario de la zona
ESTADOS_LIBERAN_HORARIO = ('Rechazada', 'Cancelada')


class ZonaForm(forms.ModelForm):
    estado = forms.TypedChoiceField(choices=[(1, _('Disponible')), (0, _('No disponible'))], coerce=int,
                                    initial=1, label=_('Estado'))

    class Meta:
        model = ZonasComunes
        fields = ['nombre', 'capacidad', 'descripcion', 'reglas', 'estado', 'valor_hora', 'ofrece_limpieza',
                  'valor_limpieza']
        labels = {'nombre': _('Nombre'), 'capacidad': _('Capacidad (personas)'), 'descripcion': _('Descripción'),
                  'reglas': _('Reglas'), 'valor_hora': _('Valor por hora (COP)'),
                  'ofrece_limpieza': _('Ofrece servicio de limpieza'), 'valor_limpieza': _('Valor de la limpieza (COP)')}
        help_texts = {
            'valor_hora': _('0 = zona gratuita. Se cobra cada hora reservada; una hora empezada cuenta completa.'),
            'valor_limpieza': _('Si el residente no lo toma, debe entregar la zona limpia o se le cobra este valor.'),
        }
        widgets = {
            'descripcion': forms.TextInput(attrs={'placeholder': _('Ej: Salón con cocina y 10 mesas')}),
            'reglas': forms.Textarea(attrs={'rows': 4, 'placeholder': _('Horarios, aforo, uso de música, aseo…')}),
            'valor_hora': forms.NumberInput(attrs={'step': '1000', 'min': '0'}),
            'valor_limpieza': forms.NumberInput(attrs={'step': '1000', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True

    def clean_capacidad(self):
        capacidad = self.cleaned_data.get('capacidad')
        if capacidad is not None and capacidad <= 0:
            raise forms.ValidationError(_('La capacidad debe ser mayor a cero.'))
        return capacidad

    def clean(self):
        cleaned_data = super().clean()
        for campo in ('valor_hora', 'valor_limpieza'):
            valor = cleaned_data.get(campo)
            if valor is not None and valor < 0:
                self.add_error(campo, _('El valor no puede ser negativo.'))
        if cleaned_data.get('ofrece_limpieza') and not cleaned_data.get('valor_limpieza'):
            self.add_error('valor_limpieza', _('Escribe el valor del servicio de limpieza.'))
        return cleaned_data


class ItemInventarioForm(forms.ModelForm):
    class Meta:
        model = ItemInventario
        fields = ['nombre', 'cantidad', 'valor_reposicion']
        labels = {'nombre': _('Implemento'), 'cantidad': _('Cantidad'), 'valor_reposicion': _('Valor de reposición (COP)')}
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': _('Ej: Parrilla a gas')}),
            'cantidad': forms.NumberInput(attrs={'min': '1'}),
            'valor_reposicion': forms.NumberInput(attrs={'step': '1000', 'min': '0'}),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 1:
            raise forms.ValidationError(_('Mínimo 1.'))
        return cantidad


InventarioFormSet = inlineformset_factory(ZonasComunes, ItemInventario, form=ItemInventarioForm,
                                          extra=2, can_delete=True)


class ReservaForm(forms.ModelForm):
    estado = forms.ChoiceField(choices=ESTADOS_RESERVA, initial='Pendiente', label=_('Estado'))

    class Meta:
        model = Reservas
        fields = ['id_zona_fk', 'id_unidad_fk', 'fecha_inicio', 'fecha_fin', 'incluye_limpieza', 'estado', 'observaciones']
        labels = {
            'incluye_limpieza': _('Incluir servicio de limpieza (si no, la zona se entrega limpia)'),
            'id_zona_fk': _('Zona común'),
            'id_unidad_fk': _('Unidad que reserva'),
            'fecha_inicio': _('Empieza'),
            'fecha_fin': _('Termina'),
            'observaciones': _('Observaciones'),
        }
        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Ej: cumpleaños, 20 invitados')}),
        }

    def __init__(self, *args, es_residente=False, **kwargs):
        super().__init__(*args, **kwargs)
        zonas = ZonasComunes.objects.order_by('nombre')
        if es_residente:
            zonas = zonas.filter(estado=1)
            # La unidad la pone la vista y el estado lo decide el administrador
            del self.fields['id_unidad_fk']
            del self.fields['estado']
        else:
            self.fields['id_unidad_fk'].required = True
            self.fields['id_unidad_fk'].queryset = Unidades.objects.order_by('torre', 'apto')
            self.fields['id_unidad_fk'].empty_label = _('Selecciona la unidad')
        self.fields['id_zona_fk'].queryset = zonas
        self.fields['id_zona_fk'].required = True
        self.fields['id_zona_fk'].empty_label = _('Selecciona una zona')
        self.fields['fecha_inicio'].required = True
        self.fields['fecha_fin'].required = True

    def clean(self):
        cleaned_data = super().clean()
        zona = cleaned_data.get('id_zona_fk')
        inicio = cleaned_data.get('fecha_inicio')
        fin = cleaned_data.get('fecha_fin')

        if not zona or not inicio or not fin:
            return cleaned_data

        if not zona.ofrece_limpieza:
            cleaned_data['incluye_limpieza'] = False

        # Al editar una reserva vieja (p. ej. para cambiarle el estado) no se exige fecha futura
        cambio_fecha = not self.instance.pk or 'fecha_inicio' in self.changed_data
        if cambio_fecha and inicio < timezone.now():
            self.add_error('fecha_inicio', _('La fecha de inicio no puede estar en el pasado.'))

        if fin <= inicio:
            self.add_error('fecha_fin', _('El fin debe ser posterior al inicio.'))
            return cleaned_data

        if (fin - inicio).total_seconds() > 12 * 3600:
            self.add_error('fecha_fin', _('Una reserva no puede durar más de 12 horas.'))

        if cleaned_data.get('estado') in ESTADOS_LIBERAN_HORARIO:
            return cleaned_data

        conflictos = (Reservas.objects
                      .filter(id_zona_fk=zona, fecha_inicio__lt=fin, fecha_fin__gt=inicio)
                      .exclude(estado__in=ESTADOS_LIBERAN_HORARIO))
        if self.instance.pk:
            conflictos = conflictos.exclude(pk=self.instance.pk)

        choque = conflictos.order_by('fecha_inicio').first()
        if choque:
            raise forms.ValidationError(
                _('%(zona)s ya está reservada de %(inicio)s a %(fin)s. Elige otro horario.') % {
                    'zona': zona,
                    'inicio': f'{timezone.localtime(choque.fecha_inicio):%d/%m %H:%M}',
                    'fin': f'{timezone.localtime(choque.fecha_fin):%H:%M}',
                }
            )

        return cleaned_data


class EntregaZonaForm(forms.Form):
    """Revisión al recibir la zona: por cada implemento, cuántos faltan y cuántos llegan dañados."""
    zona_limpia = forms.TypedChoiceField(
        label=_('¿La zona quedó limpia?'), coerce=lambda v: v == 'si',
        choices=[('si', _('Sí, quedó limpia')), ('no', _('No, quedó sucia'))],
        widget=forms.RadioSelect,
    )
    observaciones_entrega = forms.CharField(
        label=_('Observaciones'), required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': _('Ej: una silla con la pata floja; dejaron basura en la cocina')}),
    )

    def __init__(self, *args, reserva, items, **kwargs):
        super().__init__(*args, **kwargs)
        self.reserva = reserva
        self.items = list(items)
        for item in self.items:
            for tipo, etiqueta in (('faltan', _('Faltan')), ('danados', _('Dañados'))):
                self.fields[f'{tipo}_{item.pk}'] = forms.IntegerField(
                    label=f'{etiqueta}: {item.nombre}', min_value=0, max_value=item.cantidad, initial=0,
                    widget=forms.NumberInput(attrs={'min': 0, 'max': item.cantidad, 'class': 'entrada-corta'}),
                )
        if reserva.incluye_limpieza:
            # El conjunto se encarga de limpiar: no se revisa el aseo
            del self.fields['zona_limpia']

    def filas(self):
        return [(item, self[f'faltan_{item.pk}'], self[f'danados_{item.pk}']) for item in self.items]

    def clean(self):
        cleaned_data = super().clean()
        for item in self.items:
            faltan = cleaned_data.get(f'faltan_{item.pk}') or 0
            danados = cleaned_data.get(f'danados_{item.pk}') or 0
            if faltan + danados > item.cantidad:
                self.add_error(f'danados_{item.pk}', _('Entre faltantes y dañados no pueden pasar de %(n)s.')
                               % {'n': item.cantidad})
        return cleaned_data


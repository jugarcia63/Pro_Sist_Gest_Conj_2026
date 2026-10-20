from django import forms
from django.utils import timezone

from residentes.models import Unidades
from .models import Reservas, ZonasComunes
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
        fields = ['nombre', 'capacidad', 'descripcion', 'reglas', 'estado']
        labels = {'nombre': _('Nombre'), 'capacidad': _('Capacidad (personas)'), 'descripcion': _('Descripción'), 'reglas': _('Reglas')}
        widgets = {
            'descripcion': forms.TextInput(attrs={'placeholder': _('Ej: Salón con cocina y 10 mesas')}),
            'reglas': forms.Textarea(attrs={'rows': 4, 'placeholder': _('Horarios, aforo, uso de música, aseo…')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True

    def clean_capacidad(self):
        capacidad = self.cleaned_data.get('capacidad')
        if capacidad is not None and capacidad <= 0:
            raise forms.ValidationError(_('La capacidad debe ser mayor a cero.'))
        return capacidad


class ReservaForm(forms.ModelForm):
    estado = forms.ChoiceField(choices=ESTADOS_RESERVA, initial='Pendiente', label=_('Estado'))

    class Meta:
        model = Reservas
        fields = ['id_zona_fk', 'id_unidad_fk', 'fecha_inicio', 'fecha_fin', 'estado', 'observaciones']
        labels = {
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

from django import forms
from validadores import ValidacionLetrasNumerosMixin
from .models import Visitantes


class ResidenteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, residente):
        unidad = residente.id_unidad_fk
        if unidad:
            ubicacion = f"Torre {unidad.torre} - Apto {unidad.apto}"
        else:
            ubicacion = "Sin unidad asignada"
        return f"{residente.nombres} {residente.apellidos} - CC {residente.num_documento} - {ubicacion}"


class VisitanteForm(ValidacionLetrasNumerosMixin, forms.ModelForm):
    campos_solo_letras = ['nombre', 'apellidos', 'tipo_documento', 'motivo', 'estado']
    campos_solo_numeros = ['num_documento', 'telefono']

    class Meta:
        model = Visitantes
        fields = ['nombre', 'apellidos', 'tipo_documento', 'num_documento', 'telefono', 'motivo',
                  'id_residente_fk', 'fecha_ingreso', 'fecha_salida', 'estado']
        widgets = {
            'fecha_ingreso': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'id_residente_fk': 'Residente que autoriza',
        }

    id_residente_fk = ResidenteChoiceField(
        queryset=None,
        label='Residente que autoriza',
        empty_label='Selecciona un residente'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from residentes.models import Residentes
        self.fields['id_residente_fk'].queryset = Residentes.objects.select_related('id_unidad_fk').all()
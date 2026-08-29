from django import forms
from django.utils import timezone
from .models import Reservas

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reservas
        fields = ['id_zona_fk', 'id_unidad_fk', 'fecha_inicio', 'fecha_fin', 'estado', 'observaciones']
        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        zona = cleaned_data.get('id_zona_fk')
        inicio = cleaned_data.get('fecha_inicio')
        fin = cleaned_data.get('fecha_fin')

        if not zona or not inicio or not fin:
            return cleaned_data

        
        if inicio < timezone.now():
            raise forms.ValidationError("La fecha de inicio no puede ser en el pasado.")


        if fin <= inicio:
            raise forms.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")

        conflictos = Reservas.objects.filter(
            id_zona_fk=zona,
            fecha_inicio__lt=fin,
            fecha_fin__gt=inicio,
        )

        if self.instance.pk:
            conflictos = conflictos.exclude(pk=self.instance.pk)

        if conflictos.exists():
            raise forms.ValidationError("Ya existe una reserva para esa zona en ese horario.")

        return cleaned_data
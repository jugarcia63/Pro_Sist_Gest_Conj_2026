from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _

from residentes.forms import TIPOS_DOCUMENTO
from residentes.models import Residentes
from .models import Usuario

AYUDA_USUARIO = _('Con este nombre entrarás al sistema. Usa letras, números y . _ - (sin espacios).')


class CamposUsuarioMixin:
    """Valida un nombre de usuario libre (sin repetir, sin importar mayúsculas) y dos contraseñas iguales."""

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        instancia = getattr(self, 'instance', None)
        repetido = Usuario.objects.filter(username__iexact=username)
        if instancia is not None and instancia.pk:
            repetido = repetido.exclude(pk=instancia.pk)
        if repetido.exists():
            raise forms.ValidationError(_('Ese nombre de usuario ya está en uso. Elige otro.'))
        return username

    def validar_contrasenas(self, usuario):
        p1, p2 = self.cleaned_data.get('password1'), self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', _('Las dos contraseñas no coinciden.'))
        elif p1:
            try:
                password_validation.validate_password(p1, usuario)
            except forms.ValidationError as error:
                self.add_error('password1', error)


def _campo_password(etiqueta, ayuda=''):
    return forms.CharField(label=etiqueta, strip=False, help_text=ayuda,
                           widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))


class RegistroForm(CamposUsuarioMixin, forms.Form):
    """El residente crea su propia cuenta. Debe estar registrado antes por la administración."""
    tipo_documento = forms.ChoiceField(label=_('Tipo de documento'), choices=TIPOS_DOCUMENTO)
    num_documento = forms.CharField(label=_('Número de documento'), max_length=100,
                                    widget=forms.TextInput(attrs={'inputmode': 'numeric', 'placeholder': '1020304050'}))
    email = forms.EmailField(label=_('Correo electrónico'),
                             help_text=_('Si la administración registró tu correo, debe ser el mismo.'),
                             widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'tu@correo.com'}))
    username = forms.CharField(label=_('Nombre de usuario'), max_length=150, help_text=AYUDA_USUARIO,
                               validators=[UnicodeUsernameValidator()],
                               widget=forms.TextInput(attrs={'autocomplete': 'username', 'placeholder': 'laura.gomez'}))
    password1 = _campo_password(_('Contraseña'), password_validation.password_validators_help_text_html())
    password2 = _campo_password(_('Repite la contraseña'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.residente = None

    def clean(self):
        cleaned_data = super().clean()
        numero = (cleaned_data.get('num_documento') or '').strip()
        tipo = cleaned_data.get('tipo_documento')
        email = (cleaned_data.get('email') or '').strip().lower()

        if numero:
            residente = Residentes.objects.filter(num_documento=numero).select_related('usuario').first()
            if residente and residente.tipo_documento and tipo and residente.tipo_documento != tipo:
                residente = None
            if residente is None:
                self.add_error('num_documento', _('No encontramos un residente con ese documento. '
                                                  'La administración debe registrarte primero.'))
            elif residente.usuario_id:
                self.add_error('num_documento', _('Este residente ya tiene una cuenta. Inicia sesión con tu usuario.'))
            elif residente.email and email and residente.email.lower() != email:
                self.add_error('email', _('El correo no coincide con el que registró la administración.'))
            else:
                self.residente = residente

        usuario_temporal = Usuario(
            username=cleaned_data.get('username') or '', email=email,
            first_name=getattr(self.residente, 'nombres', '') or '',
            last_name=getattr(self.residente, 'apellidos', '') or '',
        )
        self.validar_contrasenas(usuario_temporal)
        return cleaned_data

    def save(self):
        residente = self.residente
        usuario = Usuario.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'].lower(),
            password=self.cleaned_data['password1'],
            first_name=residente.nombres or '',
            last_name=residente.apellidos or '',
        )
        usuario.rol = 'residente'
        usuario.save(update_fields=['rol'])
        residente.usuario = usuario
        if not residente.email:
            residente.email = usuario.email
        residente.save(update_fields=['usuario', 'email'])
        return usuario


class GuardiaForm(CamposUsuarioMixin, forms.ModelForm):
    """El administrador crea o edita una cuenta del personal de seguridad y le asigna sus credenciales."""
    password1 = _campo_password(_('Contraseña'), _('El vigilante entrará con esta contraseña.'))
    password2 = _campo_password(_('Repite la contraseña'))
    is_active = forms.BooleanField(label=_('Cuenta activa (puede iniciar sesión)'), required=False, initial=True)

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'username', 'email', 'is_active']
        labels = {
            'first_name': _('Nombres'),
            'last_name': _('Apellidos'),
            'username': _('Nombre de usuario'),
            'email': _('Correo electrónico'),
        }
        help_texts = {'username': AYUDA_USUARIO}

    def __init__(self, *args, con_password=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        if not con_password:
            del self.fields['password1']
            del self.fields['password2']

    def clean(self):
        cleaned_data = super().clean()
        if 'password1' in self.fields:
            self.validar_contrasenas(Usuario(username=cleaned_data.get('username') or '',
                                             first_name=cleaned_data.get('first_name') or '',
                                             last_name=cleaned_data.get('last_name') or ''))
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = 'seguridad'
        if 'password1' in self.fields:
            usuario.set_password(self.cleaned_data['password1'])
        if commit:
            usuario.save()
        return usuario


class AsignarPasswordForm(SetPasswordForm):
    """El administrador escribe una contraseña nueva para un residente o vigilante (nunca se genera sola)."""
    exigir_cambio = forms.BooleanField(
        label=_('Pedirle que la cambie la próxima vez que entre'), required=False, initial=True,
    )

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.debe_cambiar_password = self.cleaned_data.get('exigir_cambio', False)
        if commit:
            usuario.save()
        return usuario

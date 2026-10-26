from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _

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


def usuario_sugerido(residente):
    """laura.gomez a partir de 'Laura' 'Gómez Restrepo'; si ya existe, laura.gomez2, laura.gomez3..."""
    import unicodedata
    def limpiar(texto):
        texto = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower()
        return ''.join(c for c in texto.split()[0] if c.isalnum()) if texto.split() else ''
    base = '.'.join(p for p in (limpiar(residente.nombres), limpiar(residente.apellidos)) if p) or 'residente'
    candidato, n = base, 2
    while Usuario.objects.filter(username__iexact=candidato).exists():
        candidato, n = f'{base}{n}', n + 1
    return candidato


class CuentaResidenteForm(CamposUsuarioMixin, forms.Form):
    """El administrador crea la cuenta de un residente con una contraseña temporal.
    El residente debe cambiarla por una propia la primera vez que entre."""
    username = forms.CharField(label=_('Nombre de usuario'), max_length=150, validators=[UnicodeUsernameValidator()],
                               help_text=_('Con este nombre entrará el residente. Letras, números y . _ - (sin espacios).'),
                               widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    password1 = _campo_password(_('Contraseña temporal'),
                                _('Entrégasela al residente en persona. Al entrar, el sistema le pedirá cambiarla.'))
    password2 = _campo_password(_('Repite la contraseña'))

    def __init__(self, residente, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.residente = residente

    def clean(self):
        cleaned_data = super().clean()
        self.validar_contrasenas(Usuario(username=cleaned_data.get('username') or '',
                                         email=self.residente.email or '',
                                         first_name=self.residente.nombres or '',
                                         last_name=self.residente.apellidos or ''))
        return cleaned_data

    def save(self):
        residente = self.residente
        usuario = Usuario.objects.create_user(
            username=self.cleaned_data['username'],
            email=(residente.email or '').lower(),
            password=self.cleaned_data['password1'],
            first_name=residente.nombres or '',
            last_name=residente.apellidos or '',
        )
        usuario.rol = 'residente'
        usuario.debe_cambiar_password = True
        usuario.save(update_fields=['rol', 'debe_cambiar_password'])
        residente.usuario = usuario
        residente.save(update_fields=['usuario'])
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

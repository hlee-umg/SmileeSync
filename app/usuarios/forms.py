from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario, Rol

BASE = 'form-control'


def _estilizar(campos):
    for campo in campos.values():
        css = campo.widget.attrs.get('class', '')
        # los checkbox no llevan form-control
        if not isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs['class'] = (css + ' ' + BASE).strip()


class LoginCorreoForm(AuthenticationForm):
    """Formulario de inicio de sesión que pide el correo en vez del username."""
    username = forms.EmailField(label='Correo electrónico',
                                widget=forms.EmailInput(attrs={'autofocus': True, 'class': BASE}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs['class'] = BASE


class UsuarioCrearForm(forms.ModelForm):
    """Alta de usuario. El inicio de sesión es por correo; el username interno
    se genera a partir del correo."""
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': BASE}))
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'class': BASE}))
    respuesta_secreta = forms.CharField(label='Respuesta secreta', widget=forms.TextInput(attrs={'class': BASE}))

    class Meta:
        model = Usuario
        fields = ['email', 'first_name', 'last_name', 'telefono', 'rol', 'pregunta_secreta']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].queryset = Rol.objects.filter(estado=True)
        _estilizar(self.fields)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe un usuario con ese correo.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Las contraseñas no coinciden.')
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = self.cleaned_data['email']   # username interno = correo
        usuario.set_password(self.cleaned_data['password1'])
        usuario.set_respuesta_secreta(self.cleaned_data['respuesta_secreta'])
        if commit:
            usuario.save()
        return usuario


class UsuarioEditarForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['email', 'first_name', 'last_name', 'telefono', 'rol', 'pregunta_secreta']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].queryset = Rol.objects.filter(estado=True)
        _estilizar(self.fields)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe otro usuario con ese correo.')
        return email


# ---------- Recuperación de contraseña por pregunta secreta ----------

class RecuperarCorreoForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico',
                             widget=forms.EmailInput(attrs={'class': BASE, 'autofocus': True}))


class RecuperarRespuestaForm(forms.Form):
    respuesta = forms.CharField(label='Respuesta', widget=forms.TextInput(attrs={'class': BASE, 'autofocus': True}))


class NuevaPasswordForm(forms.Form):
    password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput(attrs={'class': BASE}))
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'class': BASE}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Las contraseñas no coinciden.')
        elif len(cleaned.get('password1', '')) < 8:
            self.add_error('password1', 'La contraseña debe tener al menos 8 caracteres.')
        return cleaned

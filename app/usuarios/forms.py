from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Rol

BASE = 'form-control'


class UsuarioCrearForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'rol']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].queryset = Rol.objects.filter(estado=True)
        for campo in self.fields.values():
            css = campo.widget.attrs.get('class', '')
            campo.widget.attrs['class'] = (css + ' ' + BASE).strip()


class UsuarioEditarForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'rol']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].queryset = Rol.objects.filter(estado=True)
        for campo in self.fields.values():
            css = campo.widget.attrs.get('class', '')
            campo.widget.attrs['class'] = (css + ' ' + BASE).strip()

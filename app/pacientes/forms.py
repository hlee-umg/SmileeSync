from django import forms
from django.utils import timezone

from config.validadores import (unificar_mensaje_email, validar_codigo,
                                 validar_email_real, validar_nombre, validar_telefono)

from .models import AntecedenteMedico, Paciente

BASE = 'form-control'


def _estilizar(campos):
    for campo in campos.values():
        css = campo.widget.attrs.get('class', '')
        if isinstance(campo.widget, (forms.Select, forms.SelectMultiple)):
            campo.widget.attrs['class'] = (css + ' form-select').strip()
        elif not isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs['class'] = (css + ' ' + BASE).strip()


def siguiente_codigo():
    """Genera el siguiente código correlativo de paciente (PAC-0001, PAC-0002...)."""
    ultimo = Paciente.objects.order_by('-id').first()
    return f'PAC-{(ultimo.id + 1) if ultimo else 1:04d}'


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['codigo', 'nombres', 'apellidos', 'fecha_nacimiento', 'sexo',
                  'telefono', 'email', 'direccion']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['codigo'].initial = siguiente_codigo()
        self.fields['codigo'].widget.attrs['readonly'] = True
        self.fields['email'].required = False
        unificar_mensaje_email(self.fields['email'])
        self.fields['telefono'].required = False
        _estilizar(self.fields)

    def clean_codigo(self):
        codigo = validar_codigo(self.cleaned_data.get('codigo'), 'código del paciente')
        existe = Paciente.objects.filter(codigo__iexact=codigo)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError('Ya existe un paciente con ese código.')
        return codigo

    def clean_nombres(self):
        return validar_nombre(self.cleaned_data.get('nombres'), 'nombre')

    def clean_apellidos(self):
        return validar_nombre(self.cleaned_data.get('apellidos'), 'apellido')

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get('telefono'))

    def clean_email(self):
        return validar_email_real(self.cleaned_data.get('email'), obligatorio=False)

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = timezone.localdate()
            if fecha > hoy:
                raise forms.ValidationError(
                    'La fecha de nacimiento no puede ser posterior al día de hoy.')
            if (hoy - fecha).days > 365 * 120:
                raise forms.ValidationError('Verifique la fecha de nacimiento ingresada.')
        return fecha


class AntecedenteMedicoForm(forms.ModelForm):
    class Meta:
        model = AntecedenteMedico
        fields = ['tipo', 'descripcion']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 2})}

    TIPOS = ['Alergia', 'Condición crónica', 'Medicamento', 'Cirugía previa',
             'Antecedente familiar', 'Observación']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'] = forms.ChoiceField(
            label='Tipo', choices=[(t, t) for t in self.TIPOS])
        _estilizar(self.fields)

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        if len(descripcion) < 5:
            raise forms.ValidationError(
                'Describa el antecedente con al menos cinco caracteres.')
        return descripcion

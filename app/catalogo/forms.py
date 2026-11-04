from django import forms

from config.validadores import validar_codigo, validar_nombre, validar_telefono
from usuarios.models import Usuario

from .models import Especialidad, Odontologo, Procedimiento, UnidadDental

BASE = "form-control"


def _estilizar(campos):
    for campo in campos.values():
        css = campo.widget.attrs.get("class", "")
        if isinstance(campo.widget, (forms.Select, forms.SelectMultiple)):
            campo.widget.attrs["class"] = (css + " form-select").strip()
        elif not isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs["class"] = (css + " " + BASE).strip()


class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ["nombre", "descripcion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["descripcion"].required = False
        _estilizar(self.fields)

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        if len(nombre) < 3:
            raise forms.ValidationError(
                "El nombre debe tener al menos tres caracteres."
            )
        existe = Especialidad.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError("Ya existe una especialidad con ese nombre.")
        return nombre


class ProcedimientoForm(forms.ModelForm):
    class Meta:
        model = Procedimiento
        fields = [
            "codigo",
            "nombre",
            "especialidad",
            "nivel_complejidad",
            "duracion_promedio_min",
            "precio",
            "descripcion",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "duracion_promedio_min": forms.NumberInput(attrs={"min": 5, "step": 5}),
            "precio": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
        }
        labels = {
            "duracion_promedio_min": "Duración promedio (minutos)",
            "precio": "Precio de lista (Q)",
        }
        help_texts = {
            "duracion_promedio_min": (
                "Valor de referencia inicial. El modelo predictivo lo ajusta "
                "conforme se acumulan atenciones reales."
            ),
            "precio": "Tarifa con que se presupuestan los planes de tratamiento.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["especialidad"].queryset = Especialidad.objects.filter(estado=True)
        self.fields["descripcion"].required = False
        self.fields["precio"].required = False
        _estilizar(self.fields)

    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio is None:
            return 0
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio

    def clean_codigo(self):
        codigo = validar_codigo(
            self.cleaned_data.get("codigo"), "código del procedimiento"
        )
        existe = Procedimiento.objects.filter(codigo__iexact=codigo)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError("Ya existe un procedimiento con ese código.")
        return codigo

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        if len(nombre) < 3:
            raise forms.ValidationError(
                "El nombre debe tener al menos tres caracteres."
            )
        return nombre

    def clean_duracion_promedio_min(self):
        duracion = self.cleaned_data.get("duracion_promedio_min")
        if duracion is not None and (duracion < 5 or duracion > 480):
            raise forms.ValidationError(
                "La duración promedio debe estar entre 5 y 480 minutos."
            )
        return duracion


class OdontologoForm(forms.ModelForm):
    class Meta:
        model = Odontologo
        fields = [
            "nombres",
            "apellidos",
            "colegiado",
            "especialidad",
            "telefono",
            "usuario",
        ]
        labels = {"usuario": "Usuario del sistema vinculado"}
        help_texts = {
            "usuario": "Permite que el profesional acceda a su agenda y registre "
            "los tiempos reales de atención.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["especialidad"].queryset = Especialidad.objects.filter(estado=True)
        self.fields["usuario"].queryset = Usuario.objects.filter(estado=True).order_by(
            "first_name"
        )
        self.fields["usuario"].required = False
        self.fields["telefono"].required = False
        self.fields["colegiado"].required = False
        _estilizar(self.fields)

    def clean_nombres(self):
        return validar_nombre(self.cleaned_data.get("nombres"), "nombre")

    def clean_apellidos(self):
        return validar_nombre(self.cleaned_data.get("apellidos"), "apellido")

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get("telefono"))

    def clean_colegiado(self):
        colegiado = (self.cleaned_data.get("colegiado") or "").strip().upper()
        if not colegiado:
            return colegiado
        existe = Odontologo.objects.filter(colegiado__iexact=colegiado)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError(
                "Ya existe un odontólogo con ese número de colegiado."
            )
        return colegiado


class UnidadDentalForm(forms.ModelForm):
    """Alta y edición de un sillón. Al gestionarse como registro del catálogo,
    incorporar una unidad nueva amplía la capacidad de la clínica sin tocar
    el código."""

    class Meta:
        model = UnidadDental
        fields = ["codigo", "nombre", "ubicacion", "observaciones"]
        labels = {"ubicacion": "Ubicación"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ("ubicacion", "observaciones"):
            self.fields[campo].required = False
        _estilizar(self.fields)

    def clean_codigo(self):
        codigo = validar_codigo(self.cleaned_data.get("codigo"), "código")
        existe = UnidadDental.objects.filter(codigo__iexact=codigo)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError("Ya existe una unidad con ese código.")
        return codigo

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        if len(nombre) < 3:
            raise forms.ValidationError(
                "El nombre debe tener al menos tres caracteres."
            )
        return nombre
